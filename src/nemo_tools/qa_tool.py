"""
NeMo QA Tool for question answering with memory context
"""
from typing import Dict, Any, List
from openai import OpenAI
from src.core.config import Config
from src.core.logging import get_logger
from src.core.rate_limiter import nvapi_rate_limiter

logger = get_logger(__name__)

class NeMoQATool:
    """Real NeMo QA tool with memory context"""
    
    def __init__(self, qa_model, memory_manager):
        """Initialize with NeMo QA model and memory manager"""
        self.qa_model = qa_model
        self.memory_manager = memory_manager
        self.model_ready = qa_model is not None
        
        # Fallback to NVIDIA API client
        config = Config()
        logger.info(f"QA Tool API key: {config.nvidia_api_key[:10]}...{config.nvidia_api_key[-4:] if config.nvidia_api_key else 'MISSING'}")
        self.client = OpenAI(
            api_key=config.nvidia_api_key,
            base_url=config.nvidia_base_url
        )
        
        logger.info(f"NeMo QA Tool initialized, model ready: {self.model_ready}")
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute question answering"""
        question = input_data.get("question", "")
        
        if not question:
            return {"success": False, "error": "No question provided"}
            
        try:
            # Use hybrid search if vector memory is available
            if hasattr(self.memory_manager, 'hybrid_search'):
                logger.info("Using hybrid vector search for QA")
                # Get more results for better context
                search_results = self.memory_manager.hybrid_search(question, limit=10)
            else:
                # Fallback to simple search
                search_results = self.memory_manager.search_memories(question, limit=10)
            
            # Also get recent memories to ensure we include latest activities
            if hasattr(self.memory_manager, 'memories'):
                recent_memories = sorted(self.memory_manager.memories, 
                                       key=lambda x: x.get('timestamp', ''), 
                                       reverse=True)[:3]
                # Add recent memories if not already in search results
                existing_ids = {m.get('id') for m in search_results}
                for mem in recent_memories:
                    if mem.get('id') not in existing_ids:
                        search_results.append(mem)
            
            context = self._build_context(search_results)
            
            logger.info(f"Answering question: {question}")
            logger.info(f"Found {len(search_results)} relevant memories")
            
            if self.model_ready:
                # Use NeMo QA model
                answer = self._answer_with_nemo(question, context)
            else:
                # Use NVIDIA API
                answer = self._answer_with_api(question, context)
                
            return {
                "success": True,
                "question": question,
                "answer": answer,
                "memories_used": len(search_results),
                "context": search_results[:3]  # Return top 3 memories
            }
            
        except Exception as e:
            logger.error(f"QA failed: {e}")
            return {
                "success": False,
                "error": f"Question answering failed: {str(e)}"
            }
            
    def _build_context(self, memories: List[Dict[str, Any]]) -> str:
        """Build context from memory search results"""
        if not memories:
            return "No relevant memories found."
            
        # Sort memories by timestamp (most recent first) if not already sorted by relevance
        # This ensures recent voice notes are prioritized
        memories_sorted = sorted(memories, 
                                key=lambda x: (x.get('relevance', 0) * 2 + 
                                             (1 if 'voice_note' in str(x.get('metadata', {})) else 0)),
                                reverse=True)
        
        context_parts = []
        for memory in memories_sorted[:7]:  # Use top 7 memories for better context
            content = memory.get("content", "")
            timestamp = memory.get("timestamp", "Unknown time")
            metadata = memory.get("metadata", {})
            
            # Add source type for better context
            source = metadata.get('source', metadata.get('type', ''))
            if source:
                context_parts.append(f"[{source}] Memory from {timestamp}: {content}")
            else:
                context_parts.append(f"Memory from {timestamp}: {content}")
            
        full_context = "\n\n".join(context_parts)
        logger.info(f"Built context with {len(context_parts)} memories")
        return full_context
        
    def _answer_with_nemo(self, question: str, context: str) -> str:
        """Answer question using NeMo QA model"""
        try:
            # Use NeMo QA model for inference
            prediction = self.qa_model.predict(
                questions=[question],
                contexts=[context]
            )
            
            answer = prediction[0] if prediction else "I couldn't find an answer in your memories."
            logger.info(f"NeMo QA answer: {answer}")
            return answer
            
        except Exception as e:
            logger.error(f"NeMo QA failed, falling back to API: {e}")
            return self._answer_with_api(question, context)
            
    def _answer_with_api(self, question: str, context: str) -> str:
        """Answer question using NVIDIA API or fallback to local response"""
        
        # If no memories found, provide helpful response
        if context == "No relevant memories found.":
            return f"I don't have any memories about '{question}' yet. Try adding some memories first by recording voice notes or uploading photos!"
        
        try:
            nvapi_rate_limiter.wait()  # Wait before making the API call
            system_prompt = """You are a caring memory assistant helping someone recall their memories and experiences. 
            IMPORTANT: Base your answer ONLY on the actual memories provided. Be accurate about specific details mentioned.
            - If the memory mentions specific foods (like pasta), include those exact details
            - If the memory mentions specific activities (like cooking, playing), mention them accurately
            - Pay special attention to voice_note memories as they are most recent
            - Be warm and personal, but accurate to what's actually in the memories
            - Do not use em dash in your response
            - If something is not mentioned in the memories, don't make it up"""
            
            user_prompt = f"""Question: {question}

Memory Context:
{context}

Please answer based on the memories provided. Be warm, personal, and helpful."""

            completion = self.client.chat.completions.create(
                model="nvidia/nvidia-nemotron-nano-9b-v2",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            
            answer = completion.choices[0].message.content
            logger.info(f"API QA answer: {answer}")
            
            # Handle None or empty response
            if not answer or answer.strip() == "":
                return "Based on your memories, here's what I found: " + context[:250]
            
            return answer
            
        except Exception as e:
            logger.error(f"API QA failed: {e}")
            # Provide intelligent fallback based on context
            if "No relevant memories" in context:
                return f"I don't have memories about '{question}' yet. Add some memories to get started!"
            else:
                # Use context directly if API fails
                return f"I encountered an error trying to answer your question, but based on your memories, here is some relevant information: {context[:250]}..."
            
