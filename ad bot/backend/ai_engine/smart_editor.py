# backend/ai_engine/smart_editor.py
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
import whisper
import logging
from typing import List, Dict, Tuple, Optional
import os
from datetime import datetime

from backend.config import WHISPER_MODEL, SUPPORTED_ASPECT_RATIOS, MAX_VIDEO_DURATION
from backend.utils.crypto_utils import generate_secure_key

logger = logging.getLogger(__name__)

class SmartEditor:
    def __init__(self):
        self.whisper_model = None
        self.scene_threshold = 30.0  # Threshold for scene detection
        
    def load_whisper(self):
        """Load Whisper model for speech recognition"""
        if self.whisper_model is None:
            try:
                self.whisper_model = whisper.load_model(WHISPER_MODEL)
                logger.info(f"Loaded Whisper model: {WHISPER_MODEL}")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
    
    def detect_scenes(self, video_path: str) -> List[Dict]:
        """Detect scenes in video using OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            scenes = []
            frame_count = 0
            prev_frame = None
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if prev_frame is not None:
                    # Calculate frame difference
                    diff = cv2.absdiff(prev_frame, frame)
                    mean_diff = np.mean(diff)
                    
                    if mean_diff > self.scene_threshold:
                        scenes.append({
                            "frame": frame_count,
                            "timestamp": frame_count / cap.get(cv2.CAP_PROP_FPS),
                            "change_score": mean_diff
                        })
                
                prev_frame = frame.copy()
                frame_count += 1
            
            cap.release()
            logger.info(f"Detected {len(scenes)} scenes")
            return scenes
            
        except Exception as e:
            logger.error(f"Scene detection error: {e}")
            return []
    
    def extract_audio_and_transcribe(self, video_path: str) -> Dict:
        """Extract audio and transcribe using Whisper"""
        try:
            self.load_whisper()
            
            # Load video and extract audio
            video = VideoFileClip(video_path)
            audio = video.audio
            
            # Save audio temporarily
            temp_audio_path = f"temp_audio_{generate_secure_key(8)}.wav"
            audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
            
            # Transcribe
            result = self.whisper_model.transcribe(temp_audio_path)
            
            # Clean up
            os.remove(temp_audio_path)
            video.close()
            
            return {
                "text": result["text"],
                "segments": result["segments"],
                "language": result["language"]
            }
            
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return {"text": "", "segments": [], "language": "en"}
    
    def find_highlight_moments(self, video_path: str, scenes: List[Dict], transcription: Dict) -> List[Dict]:
        """Find the most engaging moments in the video"""
        try:
            highlights = []
            
            # Analyze scenes for visual interest
            for scene in scenes:
                cap = cv2.VideoCapture(video_path)
                cap.set(cv2.CAP_PROP_POS_FRAMES, scene["frame"])
                ret, frame = cap.read()
                
                if ret:
                    # Calculate visual interest score
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    blur = cv2.GaussianBlur(gray, (21, 21), 0)
                    laplacian = cv2.Laplacian(blur, cv2.CV_64F)
                    variance = laplacian.var()
                    
                    highlight_score = variance + scene["change_score"]
                    
                    highlights.append({
                        "frame": scene["frame"],
                        "timestamp": scene["timestamp"],
                        "score": highlight_score,
                        "type": "visual_interest"
                    })
                
                cap.release()
            
            # Analyze transcription for speech highlights
            if transcription.get("segments"):
                for segment in transcription["segments"]:
                    # Look for keywords that indicate engagement
                    text = segment["text"].lower()
                    engagement_keywords = ["wow", "amazing", "incredible", "watch", "look", "here", "now"]
                    
                    if any(keyword in text for keyword in engagement_keywords):
                        highlights.append({
                            "frame": int(segment["start"] * 30),  # Approximate frame
                            "timestamp": segment["start"],
                            "score": 50,  # Base score for speech highlights
                            "type": "speech_highlight",
                            "text": segment["text"]
                        })
            
            # Sort by score and return top highlights
            highlights.sort(key=lambda x: x["score"], reverse=True)
            return highlights[:10]  # Return top 10 highlights
            
        except Exception as e:
            logger.error(f"Highlight detection error: {e}")
            return []
    
    def create_platform_edit(self, video_path: str, platform: str, highlights: List[Dict], 
                           transcription: Dict, duration: int = 60) -> str:
        """Create platform-specific video edit"""
        try:
            video = VideoFileClip(video_path)
            
            # Get platform aspect ratio
            aspect_ratio = SUPPORTED_ASPECT_RATIOS.get(platform, (9, 16))
            
            # Select best highlight for the edit
            if highlights:
                best_highlight = highlights[0]
                start_time = max(0, best_highlight["timestamp"] - duration/2)
                end_time = min(video.duration, start_time + duration)
            else:
                # Fallback to middle of video
                start_time = max(0, (video.duration - duration) / 2)
                end_time = start_time + duration
            
            # Cut the video
            edited_video = video.subclip(start_time, end_time)
            
            # Resize for platform
            if aspect_ratio == (9, 16):
                # Vertical format (TikTok, Shorts, Reels)
                edited_video = edited_video.resize(height=1920)
                # Center crop to 9:16
                w, h = edited_video.size
                crop_w = int(h * 9 / 16)
                x_center = w // 2
                edited_video = edited_video.crop(x1=x_center-crop_w//2, y1=0, 
                                               x2=x_center+crop_w//2, y2=h)
            elif aspect_ratio == (1, 1):
                # Square format (Instagram posts)
                edited_video = edited_video.resize(height=1080)
                w, h = edited_video.size
                crop_size = min(w, h)
                x_center = w // 2
                y_center = h // 2
                edited_video = edited_video.crop(x1=x_center-crop_size//2, y1=y_center-crop_size//2,
                                               x2=x_center+crop_size//2, y2=y_center+crop_size//2)
            
            # Add subtitles if transcription exists
            if transcription.get("segments"):
                edited_video = self.add_subtitles(edited_video, transcription["segments"], start_time)
            
            # Generate output path
            output_filename = f"edited_{platform}_{generate_secure_key(8)}.mp4"
            output_path = os.path.join("uploads", "edited", output_filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write the edited video
            edited_video.write_videofile(output_path, verbose=False, logger=None)
            
            # Clean up
            video.close()
            edited_video.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Platform edit creation error: {e}")
            raise
    
    def add_subtitles(self, video: VideoFileClip, segments: List[Dict], start_time: float) -> VideoFileClip:
        """Add subtitles to video"""
        try:
            clips = [video]
            
            for segment in segments:
                segment_start = segment["start"] - start_time
                segment_end = segment["end"] - start_time
                
                if segment_start < 0 or segment_end > video.duration:
                    continue
                
                # Create text clip
                text_clip = TextClip(
                    segment["text"],
                    fontsize=40,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    font='Arial-Bold'
                ).set_position(('center', 'bottom')).set_duration(segment_end - segment_start)
                
                clips.append(text_clip)
            
            # Composite video with subtitles
            final_video = CompositeVideoClip(clips)
            return final_video
            
        except Exception as e:
            logger.error(f"Subtitle addition error: {e}")
            return video
    
    def generate_thumbnail(self, video_path: str, highlights: List[Dict]) -> str:
        """Generate thumbnail from best highlight moment"""
        try:
            if not highlights:
                # Use middle frame
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
                ret, frame = cap.read()
                cap.release()
            else:
                # Use best highlight frame
                cap = cv2.VideoCapture(video_path)
                cap.set(cv2.CAP_PROP_POS_FRAMES, highlights[0]["frame"])
                ret, frame = cap.read()
                cap.release()
            
            if ret:
                # Generate thumbnail filename
                thumbnail_filename = f"thumbnail_{generate_secure_key(8)}.jpg"
                thumbnail_path = os.path.join("uploads", "thumbnails", thumbnail_filename)
                os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                
                # Save thumbnail
                cv2.imwrite(thumbnail_path, frame)
                return thumbnail_path
            
            return ""
            
        except Exception as e:
            logger.error(f"Thumbnail generation error: {e}")
            return ""
    
    def process_video(self, video_path: str, platforms: List[str] = None) -> Dict:
        """Main method to process video and create edits for all platforms"""
        try:
            if platforms is None:
                platforms = ["tiktok", "youtube_shorts", "instagram_reels"]
            
            # Detect scenes
            scenes = self.detect_scenes(video_path)
            
            # Transcribe audio
            transcription = self.extract_audio_and_transcribe(video_path)
            
            # Find highlights
            highlights = self.find_highlight_moments(video_path, scenes, transcription)
            
            # Generate thumbnail
            thumbnail_path = self.generate_thumbnail(video_path, highlights)
            
            # Create platform-specific edits
            edits = {}
            for platform in platforms:
                try:
                    edit_path = self.create_platform_edit(video_path, platform, highlights, transcription)
                    edits[platform] = edit_path
                except Exception as e:
                    logger.error(f"Failed to create edit for {platform}: {e}")
                    edits[platform] = None
            
            return {
                "original_video": video_path,
                "scenes": scenes,
                "transcription": transcription,
                "highlights": highlights,
                "thumbnail": thumbnail_path,
                "edits": edits,
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Video processing error: {e}")
            raise 