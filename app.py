"""===========================================
Memory Lane - Streamlit Demo
Built with NVIDIA NeMo Agent Toolkit Architecture

This demo showcases:
- NeMo-style agent and tool architecture
- Voice transcription and audio processing
- Photo memory processing
- Semantic memory search
- Reminder management
- NVIDIA Nemotron AI integration
===========================================
"""

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Page configuration - MUST be first
st.set_page_config(
    page_title="Memory Capsule",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import tempfile
from typing import List, Optional
import time
from datetime import datetime
from PIL import Image
import sys

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import Config
from src.nemo_agent import NeMoMemoryAgent
from src.tools.nvidia_asr import get_asr_client, WebAudioRecorder

# Initialize NVIDIA Parakeet ASR client
parakeet_asr = get_asr_client()


# Initialize session state
if 'agent' not in st.session_state:
    try:
        config = Config()
        if not config.nvidia_api_key:
            config.nvidia_api_key = "test-key"
        st.session_state.agent = NeMoMemoryAgent(config)
    except Exception as e:
        st.error(f"Failed to initialize Memory Lane: {e}")
        st.stop()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'demo_step' not in st.session_state:
    st.session_state.demo_step = 0

if 'memory_count' not in st.session_state:
    st.session_state.memory_count = 0

# Main title
st.title("🧠 Memory Capsule - Personalized Memory Assistant")
st.markdown("*Helping dementia patients recall memories, people, and routines using multimodal AI*")

# Main interface
tab1, tab2, tab3, tab4 = st.tabs(["📸 Upload & Chat", "🔍 Memory Search", "⏰ Reminders", "📊 Daily Summary"])

with tab1:
    st.header("Upload Memories & Chat")
    
    col1, col2 = st.columns([1, 1])
    
    # Initialize variables
    uploaded_images = []
    uploaded_audio = []
    
    with col1:
        st.subheader("Upload Photos")
        uploaded_images = st.file_uploader(
            "Choose family photos...",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            key="image_uploader"
        )
        
        # Initialize processed images tracker
        if 'processed_images' not in st.session_state:
            st.session_state.processed_images = set()
        
        # Display uploaded images
        if uploaded_images:
            # Process each uploaded image only once
            for img in uploaded_images:
                # Create unique ID for this image
                img_id = f"{img.name}_{img.size}"
                
                # Only process if not already processed
                if img_id not in st.session_state.processed_images:
                    # Save to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                        img.seek(0)
                        tmp_img.write(img.read())
                        tmp_img_path = tmp_img.name
                    
                    # Process with agent
                    with st.spinner(f"Analyzing {img.name}..."):
                        result = st.session_state.agent.process({
                            "image_path": tmp_img_path,
                            "description": f"A photo named {img.name}"
                        })
                        
                        if result.get("success"):
                            st.success(f"✅ Image analyzed and memory created: {result.get('memory_id')}")
                            st.session_state.processed_images.add(img_id)
                        else:
                            st.error(f"❌ Failed to process image: {result.get('error')}")
                    
                    # Clean up temporary file
                    os.unlink(tmp_img_path)

            # Show images in the UI
            for img in uploaded_images:
                st.image(img, caption=f"Uploaded: {img.name}", width=200)

        st.subheader("🎤 Voice & Text Notes")
        
        # Unified interface for voice and text input
        st.markdown("**Record or Type Your Memory**")
        
        # Recording state management
        if 'note_text' not in st.session_state:
            st.session_state.note_text = ""
        
        # Audio recording using Streamlit's audio_input
        st.markdown("**🎙️ Record Voice Note:**")
        audio_bytes = st.audio_input("Click to record your memory", key="memory_audio")
        
        # Track processed audio to avoid re-processing
        if 'last_memory_audio' not in st.session_state:
            st.session_state.last_memory_audio = None
        
        if audio_bytes is not None and audio_bytes != st.session_state.last_memory_audio:
            st.session_state.last_memory_audio = audio_bytes
            with st.spinner("🎤 Processing audio..."):
                try:
                    # Save audio bytes to temporary file
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                        tmp_audio.write(audio_bytes.getvalue())
                        tmp_audio_path = tmp_audio.name
                    
                    # Transcribe with ASR
                    result = parakeet_asr.transcribe_audio_file(tmp_audio_path)
                    
                    # Clean up temp file
                    os.unlink(tmp_audio_path)
                    
                    if result["success"]:
                        if result.get("text"):
                            st.session_state.note_text = result["text"]
                       
                            # Show the transcription in an info box
                            
                            # Don't clear the audio reference yet - wait for save
                        else:
                            st.info(result.get("message", "🎤 Audio recorded! Please type below."))
                    else:
                        st.info(result.get("error", "🎤 Audio recorded! Please type your memory below."))
                        
                except Exception as e:
                    st.warning(f"🎤 Audio captured. Please type your memory: {str(e)[:50]}")
        
        # # Show transcription success message after audio processing
        # if st.session_state.get('note_text'):
        
        
        # Use a form to ensure button clicks work properly
        with st.form(key="memory_form", clear_on_submit=False):
            note_text = st.text_area(
                "Your memory note (voice or typed):",
                value=st.session_state.get('note_text', ''),
                placeholder="🎤 Record audio above OR type your memory here...",
                height=100,
                key="memory_text_input"
            )
            
            # Debug info
            st.caption(f"Debug: Text length = {len(note_text) if note_text else 0}")
            
            form_col1, form_col2 = st.columns([3, 1])
            with form_col1:
                submit_button = st.form_submit_button("💾 Save Memory", use_container_width=True)
            with form_col2:
                clear_button = st.form_submit_button("🗱️ Clear", use_container_width=True)
        
        # Handle form submission outside the form context
        if submit_button:
            if note_text and note_text.strip():
                import logging
                logger = logging.getLogger(__name__)
                
                logger.info("="*60)
                logger.info("SAVE BUTTON CLICKED IN FORM!")
                logger.info(f"Note text to save: '{note_text}'")
                logger.info(f"Note text length: {len(note_text)}")
                logger.info("="*60)
                
                try:
                    # Determine if this is from voice transcription
                    memory_type = "voice_note" if st.session_state.last_memory_audio else "note"
                    metadata = {
                        "type": memory_type,
                        "timestamp": datetime.now().isoformat()
                    }
                    if memory_type == "voice_note":
                        metadata["source"] = "audio_transcription"
                    
                    memory_id = st.session_state.agent.memory_manager.store_memory(
                        content=note_text,
                        metadata=metadata
                    )
                    logger.info(f"Memory saved successfully with ID: {memory_id}")
                    total_memories = len(st.session_state.agent.memory_manager.memories)
                    st.success(f"✅ Memory saved! ID: {memory_id[:8]} | Total memories: {total_memories}")
                    st.session_state.memory_count += 1
                    # Clear the note text and audio reference for next entry
                    st.session_state.note_text = ""
                    st.session_state.last_memory_audio = None
                except Exception as e:
                    logger.error(f"ERROR SAVING: {str(e)}", exc_info=True)
                    st.error(f"❌ Failed: {str(e)}")
            else:
                st.warning("⚠️ Please enter some text first!")
        
        if clear_button:
            st.session_state.note_text = ""
            st.rerun()
    
    with col2:
        st.subheader("💬 Ask Questions")
        
        # Initialize question text state
        if 'question_text' not in st.session_state:
            st.session_state.question_text = ""
        
        # Audio input for questions
        st.markdown("**🎙️ Record Your Question:**")
        question_audio = st.audio_input("Click to ask via voice", key="question_audio")
        
        # Track processed audio to avoid re-processing
        if 'last_question_audio' not in st.session_state:
            st.session_state.last_question_audio = None
        
        if question_audio is not None and question_audio != st.session_state.last_question_audio:
            st.session_state.last_question_audio = question_audio
            with st.spinner("🎤 Processing your question..."):
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                        tmp_audio.write(question_audio.getvalue())
                        tmp_audio_path = tmp_audio.name
                    
                    result = parakeet_asr.transcribe_audio_file(tmp_audio_path)
                    os.unlink(tmp_audio_path)
                    
                    if result["success"] and result.get("text"):
                        st.session_state.question_text = result["text"]
                        st.success(f"✅ Question transcribed: {result['text']}")
                        st.rerun()  # Immediately show in text input
                    else:
                        st.info(result.get("message", "🎤 Audio recorded! Please type your question below."))
                except Exception as e:
                    st.warning("🎤 Please type your question below")
        
        # Text input for questions
        user_input = st.text_input(
            "Ask about your memories:",
            value=st.session_state.get('question_text', ''),
            placeholder="e.g., Who is in this photo? What did I do today?",
            key="user_query"
        )
        
        if st.button("Send Question", use_container_width=True):
            if user_input:
                with st.spinner("Thinking..."):
                    result = st.session_state.agent.process({"text": user_input})
                    response = result.get("message", "I'm not sure about that.")
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "user": user_input,
                        "assistant": response,
                        "timestamp": time.time()
                    })
                    st.session_state.question_text = ""  # Clear after sending
                    st.rerun()
        
        # Display chat history in a nice format
        st.divider()
        st.markdown("**💬 Conversation History**")
        
        # Create a scrollable chat area
        chat_area = st.container()
        with chat_area:
            if st.session_state.chat_history:
                for chat in st.session_state.chat_history[-10:]:  # Show last 10 messages
                    # User message with better contrast
                    st.markdown(
                        f'<div style="background-color: #E3F2FD; padding: 10px; border-radius: 10px; margin: 5px 0;">'
                        f'<b style="color: #1565C0;">👤 You:</b> <span style="color: #000000;">{chat["user"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Assistant response with better contrast
                    st.markdown(
                        f'<div style="background-color: #F5F5F5; padding: 10px; border-radius: 10px; margin: 5px 0;">'
                        f'<b style="color: #2E7D32;">🤖 Assistant:</b> <span style="color: #000000;">{chat["assistant"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No conversation yet. Start by asking a question or uploading memories!")

with tab2:
    st.header("🔍 Search Your Memories")
    
    search_query = st.text_input("Search your memories:", placeholder="e.g., family dinner, vacation, birthday")
    
    if search_query:
        with st.spinner("Searching memories..."):
            try:
                # Use agent to search memories
                from src.tools.search import SearchTool
                search_tool = SearchTool(st.session_state.agent.memory_manager)
                result = search_tool.execute({"query": search_query, "limit": 5})
                memories = result.get("memories", [])
                
                if memories:
                    st.success(f"Found {len(memories)} relevant memories:")
                    
                    for i, memory in enumerate(memories, 1):
                        with st.expander(f"Memory {i}"):
                            st.markdown(f"**Content:** {memory.get('content', 'No content')}")
                            st.markdown(f"**Date:** {memory.get('timestamp', 'Unknown time')}")
                            
                            metadata = memory.get('metadata', {})
                            if metadata.get('type'):
                                st.markdown(f"**Type:** {metadata['type']}")
                else:
                    st.info("No memories found for this search.")
                    
            except Exception as e:
                st.error(f"Search error: {str(e)}")

with tab3:
    st.header("⏰ Your Reminders")
    
    # Create new reminder
    st.subheader("Create New Reminder")
    reminder_input = st.text_input(
        "What would you like to be reminded about?",
        placeholder="e.g., Call Meera on Sunday at 6pm"
    )
    
    if st.button("Create Reminder") and reminder_input:
        with st.spinner("Creating reminder..."):
            try:
                result = st.session_state.agent.process({"text": reminder_input})
                
                if result.get("success"):
                    st.success(f"✅ {result.get('message', 'Reminder created!')}")
                else:
                    st.error(f"❌ Failed to create reminder: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Error creating reminder: {str(e)}")
    
    # Show active reminders
    st.subheader("Active Reminders")
    try:
        reminders = st.session_state.agent.memory_manager.get_active_reminders()
        
        if reminders:
            for reminder in reminders:
                with st.container():
                    st.warning(f"⏰ **{reminder.get('title', 'Reminder')}**")
                    st.markdown(f"📝 {reminder.get('description', '')}")
                    st.markdown(f"🕐 Scheduled: {reminder.get('scheduled_time', 'Not set')}")
                    st.markdown("---")
        else:
            st.info("No active reminders.")
            
    except Exception as e:
        st.error(f"Error loading reminders: {str(e)}")

with tab4:
    st.header("📊 Daily Summary")
    
    if st.button("Generate Daily Summary"):
        with st.spinner("Generating your daily summary..."):
            try:
                result = st.session_state.agent.process({"text": "What did I do today? Give me a summary."})
                summary = result.get("message", "No activities recorded today yet.")
                st.markdown("### Today's Summary")
                st.info(summary)
                
            except Exception as e:
                st.error(f"Error generating summary: {str(e)}")

# Demo completion check
if st.session_state.demo_step >= 5:
    st.balloons()
    st.success("🎉 Congratulations! You've completed the 5-minute Memory Lane demo!")
    
    with st.expander("Demo Summary"):
        st.markdown("""
        **What you've experienced:**
        
        1. ✅ **Multimodal Processing**: Uploaded photos and voice notes
        2. ✅ **Face Recognition**: System identified people in photos  
        3. ✅ **Speech Transcription**: Voice notes converted to text using Whisper
        4. ✅ **Memory Recall**: Asked "Who is this?" and got personalized responses
        5. ✅ **Daily Summaries**: Asked "What did I do today?" for activity recap
        6. ✅ **Smart Reminders**: Created "Remind me to call Meera Sundays 6pm"
        7. ✅ **Vector RAG**: All memories stored and searchable via ChromaDB
        8. ✅ **Nemotron AI**: Personalized responses using Nvidia's language model
        
        **Technical Stack Demonstrated:**
        - 🤖 **NeMo Agent Toolkit**: Modular agent and tool architecture
        - 🧠 **NVIDIA Nemotron**: Natural language understanding and generation  
        - 🎤 **Voice Transcription**: Text-to-speech and audio processing
        - 📸 **Vision Processing**: Photo analysis and memory extraction
        - 💾 **Vector Memory**: Semantic storage and retrieval
        - 🔧 **Tool System**: Modular tools for photo, audio, search, and reminders
        - 📊 **RAG Pipeline**: Retrieval-augmented generation for personalized responses
        """)

# Footer
st.markdown("---")
st.markdown(
    "🚀 **Memory Capsule** - Powered by NVIDIA NeMo Agent Toolkit | "
    "🧠 Nemotron AI | 🎤 Voice Transcription | 📸 Vision Processing | "
    "💾 Vector Memory Storage\n\n"
    "*Helping families stay connected through AI-powered memory assistance.*"
)
