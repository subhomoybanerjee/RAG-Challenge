import React from 'react';

function Sidebar({ 
  apiKey, setApiKey, docPath, 
  setDocPath, onIngest, isIngesting,
  isEngineReady, onClearHistory,
  onClearVectorDB, useReranking, setUseReranking,
}) {
  return (
    <div className="sidebar">
      <h2>configuration</h2>
      
      <div className="form-group">
        <label htmlFor="api-key">Groq api</label>
        <input
          id="api-key"
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="give api key"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="doc-path">document folder</label>
        <input
          id="doc-path"
          type="text"
          value={docPath}
          onChange={(e) => setDocPath(e.target.value)}
          placeholder="datasets/files"
        />
      </div>
      
      <button 
        onClick={onIngest} 
        disabled={isIngesting || !apiKey}
      >
        {isIngesting ? 'scanning and ingesting' : 'ingest docs'}
      </button>
      
      <div className={`status ${isEngineReady ? 'ready' : 'not-ready'}`}>
        {isEngineReady ? 'engine ready' : 'engine not ready'}
      </div>
      
      {isEngineReady && (
        <div className="form-group" style={{ marginTop: '20px' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={useReranking}
              onChange={(e) => setUseReranking(e.target.checked)}
              style={{ marginRight: '8px', width: '18px', height: '18px', cursor: 'pointer' }}
            />
            <span>Enable Reranking</span>
          </label>
        </div>
      )}
      
      <button 
        onClick={onClearVectorDB}
        style={{ marginTop: '10px', backgroundColor: '#d32f2f' }}
        disabled={!isEngineReady}
      >
        clear vector db
      </button>
      
      {isEngineReady && (
        <button 
          onClick={onClearHistory}
          style={{ marginTop: '10px', backgroundColor: '#AB3F56' }}
        >
          clear history
        </button>
      )}
    </div>
  );
}

export default Sidebar;

