import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { chatAPI, ingestAPI, statusAPI, clearHistoryAPI, clearVectorDBAPI } from './services/api';

const MAX_MESSAGES = 40;

function App() {
  const [messages, setMessages] = useState([]);
  const [apiKey, setApiKey] = useState('');
  const [docPath, setDocPath] = useState('datasets/files');
  const [isIngesting, setIsIngesting] = useState(false);
  const [isEngineReady, setIsEngineReady] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [useReranking, setUseReranking] = useState(false);

  useEffect(() => {
    checkEngineStatus();
  }, []);

  const checkEngineStatus = async () => {
    try {
      const response = await statusAPI();
      setIsEngineReady(response.data.engine_initialized && response.data.has_qa_chain);
    } catch (error) {
      console.error('error checking engine status:', error);
      setIsEngineReady(false);
    }
  };

  const handleIngest = async () => {
    if (!apiKey) {
      alert('enter api key first.');
      return;
    }

    setIsIngesting(true);
    try {
      const response = await ingestAPI(apiKey, docPath);
      if (response.data.success) {
        alert(`personalized docs ingested. ${response.data.message}`);
        setIsEngineReady(true);
        await checkEngineStatus();
      }
    } catch (error) {
      alert(`error: ${error.response?.data?.error || error.message}`);
    } finally {
      setIsIngesting(false);
    }
  };

  const handleSendMessage = async (query) => {
    if (!query.trim()) return;

    const userMessage = { role: 'user', content: query };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages.slice(-MAX_MESSAGES));

    if (!isEngineReady) {
      const errorMessage = { role: 'assistant', content: 'run ingestion from the sidebar first.' };
      setMessages([...updatedMessages, errorMessage].slice(-MAX_MESSAGES));
      return;
    }

    setIsLoading(true);
    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const response = await chatAPI(query, history, useReranking);
      
      if (response.data.success) {
        const assistantMessage = {
          role: 'assistant',
          content: response.data.answer,
          sources: response.data.sources,
          context: response.data.context
        };
        setMessages([...updatedMessages, assistantMessage].slice(-MAX_MESSAGES));
      }
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `error generating response: ${error.response?.data?.error || error.message}`
      };
      setMessages([...updatedMessages, errorMessage].slice(-MAX_MESSAGES));
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await clearHistoryAPI();
      setMessages([]);
    } catch (error) {
      console.error('error clearing history:', error);
    }
  };

  const handleClearVectorDB = async () => {
    if (!window.confirm('are you sure you want to clear all vd embeddings? this will delete all ingested documents.')) {
      return;
    }

    try {
      const response = await clearVectorDBAPI();
      if (response.data.success) {
        alert(response.data.message);
        setIsEngineReady(false);
        await checkEngineStatus();
      }
    } catch (error) {
      alert(`Error: ${error.response?.data?.error || error.message}`);
    }
  };

  return (
    <div className="app">
      <Sidebar
        apiKey={apiKey}
        setApiKey={setApiKey}
        docPath={docPath}
        setDocPath={setDocPath}
        onIngest={handleIngest}
        isIngesting={isIngesting}
        isEngineReady={isEngineReady}
        onClearHistory={handleClearHistory}
        onClearVectorDB={handleClearVectorDB}
        useReranking={useReranking}
        setUseReranking={setUseReranking}
      />
      <ChatInterface
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
}

export default App;

