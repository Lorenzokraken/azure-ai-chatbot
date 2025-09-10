import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
    // Add emojis to headers (but preserve content)
    content = content.replace(/^# (.+)$/gm, '## 🚀 $1');
    content = content.replace(/^## (.+)$/gm, '### 💡 $1');
    content = content.replace(/^### (.+)$/gm, '#### 📌 $1');
    
    // Add spacing before headers
    content = content.replace(/(\n)(#+ )/g, '\n\n$2');
    
    // Add spacing after paragraphs
    content = content.replace(/(\n\n[^#\n].*)(\n\n#)/g, '$1\n\n---\n$2');
    
    // Format blockquotes with emojis
    content = content.replace(/^> (.+)$/gm, '> 🤖 $1');
    
    // Add spacing around lists
    content = content.replace(/(\n)([+-] )/g, '\n\n$2');
    
    // Ensure proper line breaks
    content = content.replace(/\n{3,}/g, '\n\n');
    
    return content;
  };
  
  const formattedContent = formatMarkdownContent(stringContent);
  
  return (
    <ReactMarkdown 
      remarkPlugins={[remarkGfm]}
      components={{
        // Add custom styling for blockquotes
        blockquote: ({node, ...props}) => (
          <blockquote style={{ 
            borderLeft: '4px solid #10a37f', 
            paddingLeft: '16px', 
            marginLeft: '0',
            color: '#d1d5db',
            fontStyle: 'italic'
          }} {...props} />
        ),
        // Add custom styling for code blocks
        code: ({node, inline, className, children, ...props}) => {
          if (inline) {
            return (
              <code 
                style={{ 
                  backgroundColor: '#3c3c3c', 
                  padding: '2px 4px', 
                  borderRadius: '4px',
                  color: '#10a37f'
                }} 
                {...props}
              >
                {children}
              </code>
            );
          }
          return (
            <code 
              className={className} 
              style={{ 
                backgroundColor: '#3c3c3c',
                color: '#ffffff',
                padding: '16px',
                borderRadius: '8px',
                display: 'block',
                overflowX: 'auto'
              }} 
              {...props}
            >
              {children}
            </code>
          );
        },
        // Add custom styling for lists
        ul: ({node, ...props}) => (
          <ul style={{ paddingLeft: '20px' }} {...props} />
        ),
        li: ({node, ...props}) => (
          <li style={{ marginBottom: '8px' }} {...props} />
        ),
        // Add custom styling for headers
        h1: ({node, children, ...props}) => (
          <h1 style={{ 
            borderBottom: '1px solid #4b5563', 
            paddingBottom: '8px',
            marginBottom: '16px',
            color: '#ffffff'
          }} {...props}>
            {children}
          </h1>
        ),
        h2: ({node, children, ...props}) => (
          <h2 style={{ 
            marginTop: '24px',
            marginBottom: '12px',
            color: '#ffffff'
          }} {...props}>
            {children}
          </h2>
        ),
        h3: ({node, children, ...props}) => (
          <h3 style={{ 
            marginTop: '20px',
            marginBottom: '10px',
            color: '#ffffff'
          }} {...props}>
            {children}
          </h3>
        ),
        h4: ({node, children, ...props}) => (
          <h4 style={{ 
            marginTop: '16px',
            marginBottom: '8px',
            color: '#d1d5db'
          }} {...props}>
            {children}
          </h4>
        ),
        // Add custom styling for paragraphs
        p: ({node, ...props}) => (
          <p style={{ 
            marginBottom: '16px',
            lineHeight: '1.6'
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

