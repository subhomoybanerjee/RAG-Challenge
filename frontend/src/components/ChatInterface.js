import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';

function ChatInterface({ messages, onSendMessage, isLoading }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>chatty</h1>
      </div>
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            color: '#345678', 
            marginTop: '50px',
            fontSize: '1.1rem'
          }}>
            ask question about your docs
          </div>
        )}
        
        {messages.map((message, index) => (
          <Message key={index} message={message} />
        ))}
        
        {isLoading && (
          <div className="loading-indicator">
            let me think
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-container">
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <textarea
            className="chat-input"
            value={input}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="ask something about your files"
            rows="1"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!input.trim() || isLoading}
          >
            send
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatInterface;

