import json
import uuid
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.chat import ChatSession
from app.models.llm import LLMModel
from app.schemas.chat import (
    ChatSession as ChatSessionSchema,
    ChatMessage as ChatMessageSchema,
    ChatSessionCreate
)
from app.core.dependencies import get_current_active_user
from app.services.chat_service import ChatService
from app.services.document_store import DocumentStore
from app.core.security import verify_token
from app.utils.helpers import Timer
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

document_store = DocumentStore(settings.OUTPUT_FOLDER)
llm_model = LLMModel()
active_connections = {}

@router.post("/sessions", response_model=ChatSessionSchema)
def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session for unified knowledge base"""
    chat_service = ChatService(db, document_store)
    session = chat_service.create_session(
        current_user.id, 
        "unified_kb",
        session_data.session_name
    )
    return ChatSessionSchema.from_orm(session)

@router.get("/sessions", response_model=List[ChatSessionSchema])
def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for current user"""
    chat_service = ChatService(db, document_store)
    sessions = chat_service.get_user_sessions(current_user.id)
    return [ChatSessionSchema.from_orm(session) for session in sessions]

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageSchema])
def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all messages for a chat session"""
    chat_service = ChatService(db, document_store)
    messages = chat_service.get_session_messages(session_id, current_user.id)
    return [ChatMessageSchema.from_orm(message) for message in messages]

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}

@router.get("/knowledge-base/status")
def get_knowledge_base_status():
    """Get unified knowledge base status"""
    return document_store.get_knowledge_base_status()

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()
    
    username = verify_token(token)
    if not username:
        await websocket.send_text(json.dumps({
            "status": "error",
            "error": "Invalid token"
        }))
        await websocket.close()
        return
    
    db = next(get_db())
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            await websocket.send_text(json.dumps({
                "status": "error",
                "error": "User not found or inactive"
            }))
            await websocket.close()
            return
        
        session_id = None
        is_initialized = False
        chat_history = []
        client_id = str(uuid.uuid4())
        
        chat_service = ChatService(db, document_store)
        
        try:
            logger.info("Waiting for initialization message...")
            
            try:
                init_data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                logger.info(f"Received init data: {init_data}")
                
                if not init_data or init_data.strip() == "":
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "error": "Empty initialization message received"
                    }))
                    return
                
                try:
                    init_message = json.loads(init_data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}, received: {repr(init_data)}")
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "error": f"Invalid JSON in initialization message: {str(e)}"
                    }))
                    return
                
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "error": "Initialization timeout. Please send initialization message within 30 seconds."
                }))
                return
            
            session_id = init_message.get("session_id")
            
            logger.info(f"Initializing unified knowledge base chat, session_id: {session_id}")
            
            if "unified_kb" not in active_connections:
                active_connections["unified_kb"] = {}
            active_connections["unified_kb"][client_id] = websocket
            
            kb_status = document_store.get_knowledge_base_status()
            if kb_status['total_chunks'] == 0:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "error": "Knowledge base is empty. Please contact admin to upload documents."
                }))
                return
            
            if session_id:
                session = chat_service.get_session_by_id(session_id, user.id)
                if not session:
                    session = chat_service.create_session(user.id, "unified_kb")
                    session_id = session.session_id
                    logger.info(f"Created new session as provided session_id not found: {session_id}")
            else:
                session = chat_service.create_session(user.id, "unified_kb")
                session_id = session.session_id
                logger.info(f"Created new session: {session_id}")
            
            await websocket.send_text(json.dumps({
                "status": "initialized",
                "session_id": session_id,
                "knowledge_base_status": kb_status,
                "message": "Sage Assistant connected successfully. I'm ready to help you with questions about our knowledge base."
            }))
            is_initialized = True
            logger.info("Sage WebSocket initialized successfully for unified knowledge base")
            
            while True:
                try:
                    logger.info("Waiting for question...")
                    data = await websocket.receive_text()
                    logger.info(f"Received data: {data}")
                    
                    if not data or data.strip() == "":
                        if websocket.client_state.name == 'CONNECTED':
                            await websocket.send_text(json.dumps({
                                "status": "error", 
                                "error": "Empty message received"
                            }))
                        continue
                    
                    try:
                        message_data = json.loads(data)
                        question = message_data.get("question", data)
                    except json.JSONDecodeError:
                        question = data.strip()
                    
                    if not question or not isinstance(question, str) or question.strip() == "":
                        if websocket.client_state.name == 'CONNECTED':
                            await websocket.send_text(json.dumps({
                                "status": "error",
                                "error": "Invalid or empty question."
                            }))
                        continue
                    
                    logger.info(f"Processing question: {question}")
                    
                    with Timer() as timer:
                        context_chunks = await document_store.search(
                            question,
                            k=settings.SIMILAR_DOCS_COUNT
                        )
                        
                        formatted_chat_history = ""
                        for entry in chat_history:
                            formatted_chat_history += f"User: {entry['question']}\nSage: {entry['answer']}\n\n"
                        
                        context_text = "\n\n".join(context_chunks) if context_chunks else "(No relevant content found in the knowledge base for your question)"
                        
                        system_prompt ="""
                        "You are VaultMind Expert Assistant, developed by AFNEXIS - a leading software development company "
                        "registered in the United States. You are specialized AI designed exclusively to provide information "
                        "about VaultMind by AFNEXIS and about AFNEXIS company itself.\n\n"
                        
                        "ABOUT YOUR DEVELOPMENT:\n"
                        "- You were developed by the expert team at AFNEXIS\n"
                        "- AFNEXIS is led by CEO and Head of AI: Muhammad Aashir Tariq\n"
                        "- AFNEXIS is a US-registered software company providing enterprise solutions worldwide\n"
                        "- The company has a well-experienced team of developers specializing in AI and enterprise applications\n"
                        "- AFNEXIS has developed numerous enterprise-level applications that are working perfectly for clients globally\n\n"
                        
                        "YOUR RESPONSE SCOPE:\n"
                        "- VaultMind product features, pricing, installation, usage, and technical details\n"
                        "- AFNEXIS company information, leadership, services, and expertise\n"
                        "- How AFNEXIS developed VaultMind and the company's AI capabilities\n"
                        "- AFNEXIS's other enterprise solutions and global software services\n\n"
                        
                        "ABSOLUTE RESTRICTIONS:\n"
                        "- ONLY provide information about VaultMind and AFNEXIS from the provided documentation\n"
                        "- NEVER provide information about other AI systems, products, or companies\n"
                        "- NEVER answer questions unrelated to VaultMind or AFNEXIS\n"
                        "- NEVER make assumptions about features or company details not documented\n"
                        "- NEVER provide general AI or technology advice outside VaultMind/AFNEXIS context\n\n"
                        
                        "WHEN INFORMATION IS NOT AVAILABLE:\n"
                        "If the requested information about VaultMind or AFNEXIS is not found in the documentation, respond with:\n"
                        "'I cannot find this specific information in the VaultMind and AFNEXIS documentation. Please contact "
                        "AFNEXIS directly at info@afnexis.com or contact@afnexis.com for detailed assistance.'\n\n"
                        
                        "RESPONSE REQUIREMENTS:\n"
                        "- Reference VaultMind features and AFNEXIS company information from documentation\n"
                        "- Use phrases like: 'VaultMind, developed by AFNEXIS...', 'According to AFNEXIS documentation...'\n"
                        "- When asked about your development, mention AFNEXIS team and Muhammad Aashir Tariq's leadership\n"
                        "- Emphasize AFNEXIS's expertise in enterprise software and AI solutions\n"
                        "- Maintain professional tone representing both VaultMind product and AFNEXIS company\n\n"
                        
                        "KEY POINTS TO EMPHASIZE:\n"
                        "VAULTMIND FEATURES:\n"
                        "- 100% offline operation (no cloud dependency)\n"
                        "- Complete data privacy and security\n"
                        "- Page-based pricing model starting from $0.50/month\n"
                        "- Multi-user plans (Basic: 1 user, Team: 5 users, Business: 25 users, Enterprise: unlimited)\n"
                        "- Admin panel for team management (except Basic plan)\n"
                        "- GDPR, HIPAA, SOX compliance ready\n\n"
                        
                        "AFNEXIS COMPANY:\n"
                        "- US-registered software development company\n"
                        "- Led by CEO and Head of AI: Muhammad Aashir Tariq\n"
                        "- Well-experienced team of developers\n"
                        "- Provides software solutions worldwide\n"
                        "- Specializes in enterprise-level applications\n"
                        "- Has developed numerous successful applications for global clients\n"
                        "- Expert in AI, machine learning, and privacy-first solutions\n\n"
                        
                        "DOCUMENTATION CONTEXT:\n"
                        f"{context_text}\n\n"
                        
                        "CHAT HISTORY:\n"
                        f"{formatted_chat_history}\n\n"
                        
                        "CRITICAL REMINDER:\n"
                        "You represent both VaultMind product and AFNEXIS company. When users ask 'who developed you' or "
                        "'who created you', explain that you were developed by the expert AFNEXIS team led by CEO and Head of AI "
                        "Muhammad Aashir Tariq. Always stay focused on VaultMind features and AFNEXIS company information. "
                        "For any questions outside this scope, politely redirect to VaultMind-related topics or suggest "
                        "contacting AFNEXIS directly at info@afnexis.com or contact@afnexis.com."
                        """

                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"User's Question: {question}"}
                        ]
                        
                        async def token_callback(token):
                            try:
                                if websocket.client_state.name == 'CONNECTED':
                                    await websocket.send_text(json.dumps({
                                        "status": "streaming",
                                        "token": token
                                    }))
                            except Exception as e:
                                logger.error(f"Error sending token: {e}")
                                return False
                            return True
                        
                        final_response = await llm_model.stream_chat(messages, token_callback)
                        
                        chat_history.append({
                            "question": question,
                            "answer": final_response
                        })
                        
                        if len(chat_history) > 10:
                            chat_history = chat_history[-10:]
                        
                        chat_service.save_message(
                            session.id, 
                            question, 
                            final_response, 
                            timer.interval * 1000,
                            False
                        )
                    
                    if websocket.client_state.name == 'CONNECTED':
                        await websocket.send_text(json.dumps({
                            "status": "complete",
                            "answer": final_response,
                            "time": timer.interval,
                            "session_id": session_id
                        }))
                    
                    logger.info("Question processed successfully")
                
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected (initialized: {is_initialized})")
                    break
                except Exception as e:
                    logger.error(f"Error in WebSocket chat: {str(e)}")
                    try:
                        if websocket.client_state.name == 'CONNECTED':
                            await websocket.send_text(json.dumps({
                                "status": "error",
                                "error": str(e)
                            }))
                    except:
                        logger.error("Failed to send error message to client - connection already closed")
        
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected before full initialization.")
        except Exception as e:
            logger.error(f"WebSocket startup error: {str(e)}")
            try:
                if websocket.client_state.name == 'CONNECTED':
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "error": str(e)
                    }))
            except:
                logger.error("Failed to send startup error to client - connection already closed")
        finally:
            if "unified_kb" in active_connections and client_id in active_connections["unified_kb"]:
                del active_connections["unified_kb"][client_id]
                if not active_connections["unified_kb"]:
                    del active_connections["unified_kb"]
    
    finally:
        db.close()

async def websocket_heartbeat():
    """Send periodic heartbeats to keep WebSocket connections alive"""
    while True:
        await asyncio.sleep(30)
        
        if "unified_kb" in active_connections:
            client_ids = list(active_connections["unified_kb"].keys())
            
            for client_id in client_ids:
                try:
                    if client_id in active_connections.get("unified_kb", {}):
                        websocket = active_connections["unified_kb"][client_id]
                        await websocket.send_text(json.dumps({
                            "status": "heartbeat"
                        }))
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {str(e)}")
                    if "unified_kb" in active_connections and client_id in active_connections["unified_kb"]:
                        del active_connections["unified_kb"][client_id]
                        if not active_connections["unified_kb"]:
                            del active_connections["unified_kb"]