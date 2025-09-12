import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CodeBlock from './CodeBlock';

// 1. Error Boundary Component
// This class component will catch rendering errors in its children.
class MarkdownErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // You can also log the error to an error reporting service
    console.error("Error rendering Markdown:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return <pre>Error: Impossibile renderizzare questo contenuto.</pre>;
    }

    return this.props.children;
  }
}

// 2. Memoized Markdown Renderer Component
// This component handles the actual rendering and is wrapped by the Error Boundary.
const MemoizedMarkdownRenderer = React.memo(({ content }) => {
  // More robust content sanitization to handle objects and other types
  let sanitizedContent;
  
  if (typeof content === 'string') {
    sanitizedContent = content;
  } else if (content === null || content === undefined) {
    sanitizedContent = '';
  } else if (typeof content === 'object') {
    // Handle objects and arrays
    try {
      sanitizedContent = JSON.stringify(content, null, 2);
    } catch (e) {
      sanitizedContent = "[Contenuto non serializzabile]";
    }
  } else if (typeof content.toString === 'function') {
    sanitizedContent = content.toString();
  } else {
    sanitizedContent = String(content);
  }
  
  // Ensure we always have a valid string
  const stringContent = sanitizedContent || '';
  
  // Additional check to ensure we're not passing undefined
  if (stringContent === undefined || stringContent === null) {
    return <div>Contenuto vuoto</div>;
  }
  
  // Function to format the markdown content with emojis and better spacing
  const formatMarkdownContent = (content) => {
    // Preserve existing headers but don't add emojis (we'll add them in components)
    
    // Add spacing before headers
    content = content.replace(/(\n)(#{1,6} )/g, '\n\n$2');
    
    // Add spacing around code blocks
    content = content.replace(/(\n)(```)/g, '\n\n$2');
    content = content.replace(/(```\n)/g, '$1\n');
    
    // Add spacing around lists
    content = content.replace(/(\n)([*+-] )/g, '\n\n$2');
    content = content.replace(/(\n)(\d+\. )/g, '\n\n$2');
    
    // Add spacing around blockquotes
    content = content.replace(/(\n)(> )/g, '\n\n$2');
    
    // Add spacing around horizontal rules
    content = content.replace(/(\n)(---)/g, '\n\n$2');
    content = content.replace(/(---\n)/g, '$1\n');
    
    // Ensure proper line breaks (max 2 consecutive newlines)
    content = content.replace(/\n{3,}/g, '\n\n');
    
    // Trim whitespace at start and end
    content = content.trim();
    
    return content;
  };
  
  const formattedContent = formatMarkdownContent(stringContent);
  
  return (
    <ReactMarkdown 
      remarkPlugins={[remarkGfm]}
      components={{
        // Custom code component with syntax highlighting
        code: ({node, inline, className, children, ...props}) => {
          if (inline) {
            return (
              <code 
                style={{ 
                  backgroundColor: '#3c3c3c', 
                  padding: '2px 6px', 
                  borderRadius: '4px',
                  color: '#10a37f',
                  fontSize: '0.9em',
                  fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace'
                }} 
                {...props}
              >
                {children}
              </code>
            );
          }
          return (
            <CodeBlock className={className} {...props}>
              {children}
            </CodeBlock>
          );
        },
        // Enhanced styling for blockquotes
        blockquote: ({node, ...props}) => (
          <blockquote style={{ 
            borderLeft: '4px solid #10a37f', 
            paddingLeft: '16px', 
            marginLeft: '0',
            marginRight: '0',
            marginTop: '16px',
            marginBottom: '16px',
            color: '#d1d5db',
            fontStyle: 'italic',
            backgroundColor: '#1a1a1a',
            padding: '12px 16px',
            borderRadius: '0 8px 8px 0'
          }} {...props} />
        ),
        // Enhanced styling for lists
        ul: ({node, ...props}) => (
          <ul style={{ 
            paddingLeft: '20px',
            marginBottom: '16px',
            listStyleType: '• '
          }} {...props} />
        ),
        ol: ({node, ...props}) => (
          <ol style={{ 
            paddingLeft: '20px',
            marginBottom: '16px'
          }} {...props} />
        ),
        li: ({node, ...props}) => (
          <li style={{ 
            marginBottom: '8px',
            lineHeight: '1.6'
          }} {...props} />
        ),
        // Enhanced styling for headers with better spacing and colors
        h1: ({node, children, ...props}) => (
          <h1 style={{ 
            borderBottom: '2px solid #10a37f', 
            paddingBottom: '8px',
            marginTop: '32px',
            marginBottom: '20px',
            color: '#ffffff',
            fontSize: '2em',
            fontWeight: 'bold'
          }} {...props}>
            🚀 {children}
          </h1>
        ),
        h2: ({node, children, ...props}) => (
          <h2 style={{ 
            marginTop: '28px',
            marginBottom: '16px',
            color: '#ffffff',
            fontSize: '1.5em',
            fontWeight: 'bold',
            borderLeft: '4px solid #10a37f',
            paddingLeft: '12px'
          }} {...props}>
            💡 {children}
          </h2>
        ),
        h3: ({node, children, ...props}) => (
          <h3 style={{ 
            marginTop: '24px',
            marginBottom: '12px',
            color: '#ffffff',
            fontSize: '1.25em',
            fontWeight: 'bold'
          }} {...props}>
            📌 {children}
          </h3>
        ),
        h4: ({node, children, ...props}) => (
          <h4 style={{ 
            marginTop: '20px',
            marginBottom: '10px',
            color: '#d1d5db',
            fontSize: '1.1em',
            fontWeight: 'bold'
          }} {...props}>
            ▶️ {children}
          </h4>
        ),
        h5: ({node, children, ...props}) => (
          <h5 style={{ 
            marginTop: '16px',
            marginBottom: '8px',
            color: '#d1d5db',
            fontSize: '1em',
            fontWeight: 'bold'
          }} {...props}>
            🔸 {children}
          </h5>
        ),
        h6: ({node, children, ...props}) => (
          <h6 style={{ 
            marginTop: '14px',
            marginBottom: '6px',
            color: '#9ca3af',
            fontSize: '0.9em',
            fontWeight: 'bold'
          }} {...props}>
            🔹 {children}
          </h6>
        ),
        // Enhanced styling for paragraphs
        p: ({node, ...props}) => (
          <p style={{ 
            marginBottom: '16px',
            lineHeight: '1.7',
            color: '#e5e7eb'
          }} {...props} />
        ),
        // Enhanced styling for tables
        table: ({node, ...props}) => (
          <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              backgroundColor: '#1a1a1a',
              borderRadius: '8px',
              overflow: 'hidden'
            }} {...props} />
          </div>
        ),
        thead: ({node, ...props}) => (
          <thead style={{
            backgroundColor: '#2d2d2d'
          }} {...props} />
        ),
        th: ({node, ...props}) => (
          <th style={{
            padding: '12px',
            textAlign: 'left',
            borderBottom: '2px solid #10a37f',
            color: '#ffffff',
            fontWeight: 'bold'
          }} {...props} />
        ),
        td: ({node, ...props}) => (
          <td style={{
            padding: '12px',
            borderBottom: '1px solid #404040',
            color: '#e5e7eb'
          }} {...props} />
        ),
        // Enhanced styling for horizontal rules
        hr: ({node, ...props}) => (
          <hr style={{
            border: 'none',
            height: '2px',
            background: 'linear-gradient(to right, transparent, #10a37f, transparent)',
            margin: '24px 0'
          }} {...props} />
        ),
        // Enhanced styling for links
        a: ({node, ...props}) => (
          <a style={{
            color: '#10a37f',
            textDecoration: 'underline',
            textDecorationStyle: 'dotted'
          }} {...props} />
        ),
        // Enhanced styling for strong/bold text
        strong: ({node, ...props}) => (
          <strong style={{
            color: '#ffffff',
            fontWeight: 'bold'
          }} {...props} />
        ),
        // Enhanced styling for emphasis/italic text
        em: ({node, ...props}) => (
          <em style={{
            color: '#d1d5db',
            fontStyle: 'italic'
          }} {...props} />
        )
      }}
    >
      {formattedContent}
    </ReactMarkdown>
  );
});

// 3. Main Component to be exported
// This component combines the Error Boundary and the Renderer.
const MarkdownRenderer = ({ content }) => {
  // Ensure content is a string before passing it down
  let stringContent;
  
  if (typeof content === 'string') {
    stringContent = content;
  } else if (content === null || content === undefined) {
    stringContent = '';
  } else if (typeof content === 'object') {
    // Handle objects and arrays
    try {
      stringContent = JSON.stringify(content, null, 2);
    } catch (e) {
      stringContent = "[Contenuto non serializzabile]";
    }
  } else if (typeof content.toString === 'function') {
    stringContent = content.toString();
  } else {
    stringContent = String(content);
  }
  
  // Additional check to ensure we're not passing undefined
  if (stringContent === undefined || stringContent === null) {
    return <div>Contenuto vuoto</div>;
  }
  
  return (
    <MarkdownErrorBoundary>
      <MemoizedMarkdownRenderer content={stringContent} />
    </MarkdownErrorBoundary>
  );
};

export default MarkdownRenderer;

