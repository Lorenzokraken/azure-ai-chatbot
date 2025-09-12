import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeBlock = ({ children, className, ...props }) => {
  const [copied, setCopied] = useState(false);
  
  // Extract language from className (format: "language-python" -> "python")
  const language = className ? className.replace('language-', '') : 'text';
  
  // Get the code content
  const code = String(children).replace(/\n$/, '');

  // Copy to clipboard function
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div style={{ position: 'relative', marginBottom: '16px' }}>
      {/* Header with language and copy button */}
      <div style={{
        backgroundColor: '#2d2d2d',
        padding: '8px 16px',
        borderTopLeftRadius: '8px',
        borderTopRightRadius: '8px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid #404040'
      }}>
        <span style={{
          color: '#9ca3af',
          fontSize: '12px',
          fontWeight: 'bold',
          textTransform: 'uppercase'
        }}>
          {language}
        </span>
        <button
          onClick={copyToClipboard}
          style={{
            backgroundColor: copied ? '#10a37f' : '#404040',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '4px 8px',
            fontSize: '12px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            transition: 'background-color 0.2s'
          }}
          onMouseEnter={(e) => {
            if (!copied) e.target.style.backgroundColor = '#525252';
          }}
          onMouseLeave={(e) => {
            if (!copied) e.target.style.backgroundColor = '#404040';
          }}
        >
          {copied ? (
            <>
              <span>✓</span>
              <span>Copiato!</span>
            </>
          ) : (
            <>
              <span>📋</span>
              <span>Copia</span>
            </>
          )}
        </button>
      </div>
      
      {/* Code content with syntax highlighting */}
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderTopLeftRadius: 0,
          borderTopRightRadius: 0,
          borderBottomLeftRadius: '8px',
          borderBottomRightRadius: '8px',
          fontSize: '14px',
          lineHeight: '1.5'
        }}
        showLineNumbers={true}
        lineNumberStyle={{
          color: '#6b7280',
          fontSize: '12px',
          paddingRight: '16px'
        }}
        {...props}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
};

export default CodeBlock;
