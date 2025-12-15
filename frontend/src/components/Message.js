import React, { useState } from 'react';

function Message({ message }) {
  const [showContext, setShowContext] = useState(false);

  const formatContent = (text) => {
    if (!text) return '';
    return text.split('\n').map((line, index, array) => (
      <React.Fragment key={index}>
        {line}
        {index < array.length - 1 && <br />}
      </React.Fragment>
    ));
  };

  return (
    <div className={`message ${message.role}`}>
      <div className="message-content">
        {formatContent(message.content)}
      </div>
      
      {message.sources && message.sources.length > 0 && (
        <div className="message-sources">
          sources: {message.sources.join(', ')}
        </div>
      )}
      
      {message.context && (
        <>
          <button 
            className="context-toggle"
            onClick={() => setShowContext(!showContext)}
          >
            {showContext ? 'hide' : 'view'} retrieved context
          </button>
          
          {showContext && (
            <div className="message-context">
              {formatContent(message.context)}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Message;

