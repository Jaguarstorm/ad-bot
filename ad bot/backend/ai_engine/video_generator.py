# backend/ai_engine/video_generator.py
import openai
import httpx
import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from backend.config import OPENAI_API_KEY, ELEVENLABS_API_KEY, GPT_MODEL, MAX_TOKENS, TEMPERATURE
from backend.utils.crypto_utils import generate_secure_key

logger = logging.getLogger(__name__)

class VideoGenerator:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        self.elevenlabs_api_key = ELEVENLABS_API_KEY
        
    async def generate_script(self, topic: str, duration: int = 60, style: str = "engaging") -> Dict:
        """Generate video script using GPT"""
        try:
            prompt = f"""
            Create a {duration}-second video script about "{topic}". 
            Style: {style}
            
            Requirements:
            - Engaging and attention-grabbing
            - Suitable for social media (TikTok, YouTube Shorts, Instagram)
            - Include hooks and call-to-action
            - Break into clear segments with timestamps
            - Maximum 150 words total
            
            Format the response as JSON with:
            {{
                "title": "Video title",
                "script": "Full script text",
                "segments": [
                    {{
                        "start": 0,
                        "end": 15,
                        "text": "Opening hook"
                    }}
                ],
                "hashtags": ["relevant", "hashtags"],
                "description": "Video description"
            }}
            """
            
            response = openai.ChatCompletion.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional video script writer specializing in short-form social media content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            script_data = json.loads(response.choices[0].message.content)
            logger.info(f"Generated script for topic: {topic}")
            return script_data
            
        except Exception as e:
            logger.error(f"Script generation error: {e}")
            raise
    
    async def generate_voiceover(self, script: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> str:
        """Generate voiceover using ElevenLabs"""
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            
            data = {
                "text": script,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    # Save audio file
                    audio_filename = f"voiceover_{generate_secure_key(8)}.mp3"
                    audio_path = os.path.join("uploads", "voiceovers", audio_filename)
                    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                    
                    with open(audio_path, "wb") as f:
                        f.write(response.content)
                    
                    logger.info(f"Generated voiceover: {audio_path}")
                    return audio_path
                else:
                    raise Exception(f"ElevenLabs API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Voiceover generation error: {e}")
            raise
    
    async def fetch_stock_footage(self, query: str, count: int = 5) -> List[str]:
        """Fetch stock footage from Pexels API"""
        try:
            # Using Pexels API for stock footage
            pexels_api_key = os.getenv("PEXELS_API_KEY")
            if not pexels_api_key:
                logger.warning("Pexels API key not found, using placeholder footage")
                return []
            
            url = f"https://api.pexels.com/videos/search?query={query}&per_page={count}"
            headers = {"Authorization": pexels_api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    video_urls = []
                    
                    for video in data.get("videos", []):
                        # Get the smallest video file for faster processing
                        video_files = video.get("video_files", [])
                        if video_files:
                            smallest_file = min(video_files, key=lambda x: x.get("width", 0))
                            video_urls.append(smallest_file["link"])
                    
                    return video_urls[:count]
                else:
                    logger.warning(f"Pexels API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Stock footage fetch error: {e}")
            return []
    
    async def create_video_from_script(self, script_data: Dict, voiceover_path: str, 
                                     stock_footage: List[str] = None) -> str:
        """Create final video by combining voiceover and footage"""
        try:
            from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
            
            # Load voiceover
            audio = AudioFileClip(voiceover_path)
            duration = audio.duration
            
            # Create video clips
            video_clips = []
            
            if stock_footage:
                # Use stock footage
                for i, video_url in enumerate(stock_footage):
                    try:
                        # Download and load video
                        video_filename = f"stock_{generate_secure_key(8)}.mp4"
                        video_path = os.path.join("uploads", "temp", video_filename)
                        os.makedirs(os.path.dirname(video_path), exist_ok=True)
                        
                        async with httpx.AsyncClient() as client:
                            response = await client.get(video_url)
                            with open(video_path, "wb") as f:
                                f.write(response.content)
                        
                        # Load video clip
                        clip = VideoFileClip(video_path)
                        video_clips.append(clip)
                        
                    except Exception as e:
                        logger.error(f"Failed to load stock footage {i}: {e}")
                        continue
            else:
                # Create placeholder video with text
                placeholder = TextClip(
                    script_data["title"],
                    fontsize=60,
                    color='white',
                    bg_color='black',
                    size=(1080, 1920)
                ).set_duration(duration)
                video_clips.append(placeholder)
            
            # Combine video clips
            if len(video_clips) > 1:
                # Distribute clips across duration
                clip_duration = duration / len(video_clips)
                for i, clip in enumerate(video_clips):
                    start_time = i * clip_duration
                    end_time = min((i + 1) * clip_duration, duration)
                    video_clips[i] = clip.subclip(0, end_time - start_time)
                
                video = concatenate_videoclips(video_clips)
            else:
                video = video_clips[0]
            
            # Add subtitles
            if script_data.get("segments"):
                video = self.add_subtitles_to_generated_video(video, script_data["segments"])
            
            # Combine video and audio
            final_video = video.set_audio(audio)
            
            # Generate output path
            output_filename = f"generated_{generate_secure_key(8)}.mp4"
            output_path = os.path.join("uploads", "generated", output_filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write final video
            final_video.write_videofile(output_path, verbose=False, logger=None)
            
            # Clean up
            audio.close()
            video.close()
            final_video.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video creation error: {e}")
            raise
    
    def add_subtitles_to_generated_video(self, video, segments: List[Dict]):
        """Add subtitles to generated video"""
        try:
            clips = [video]
            
            for segment in segments:
                start_time = segment["start"]
                end_time = segment["end"]
                text = segment["text"]
                
                # Create text clip
                text_clip = TextClip(
                    text,
                    fontsize=40,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    font='Arial-Bold'
                ).set_position(('center', 'bottom')).set_duration(end_time - start_time)
                
                clips.append(text_clip)
            
            # Composite video with subtitles
            final_video = CompositeVideoClip(clips)
            return final_video
            
        except Exception as e:
            logger.error(f"Subtitle addition error: {e}")
            return video
    
    async def generate_complete_video(self, topic: str, duration: int = 60, 
                                    style: str = "engaging", voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> Dict:
        """Generate complete video from topic"""
        try:
            # Step 1: Generate script
            script_data = await self.generate_script(topic, duration, style)
            
            # Step 2: Generate voiceover
            voiceover_path = await self.generate_voiceover(script_data["script"], voice_id)
            
            # Step 3: Fetch stock footage
            stock_footage = await self.fetch_stock_footage(topic, count=3)
            
            # Step 4: Create final video
            video_path = await self.create_video_from_script(script_data, voiceover_path, stock_footage)
            
            return {
                "topic": topic,
                "script": script_data,
                "voiceover_path": voiceover_path,
                "video_path": video_path,
                "stock_footage": stock_footage,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Complete video generation error: {e}")
            raise
    
    def get_available_voices(self) -> List[Dict]:
        """Get available ElevenLabs voices"""
        try:
            url = "https://api.elevenlabs.io/v1/voices"
            headers = {"xi-api-key": self.elevenlabs_api_key}
            
            response = httpx.get(url, headers=headers)
            
            if response.status_code == 200:
                voices = response.json().get("voices", [])
                return [
                    {
                        "id": voice["voice_id"],
                        "name": voice["name"],
                        "category": voice.get("category", "general")
                    }
                    for voice in voices
                ]
            else:
                logger.error(f"Failed to fetch voices: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Voice fetch error: {e}")
            return [] 