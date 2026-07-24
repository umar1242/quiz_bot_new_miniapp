import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Props {
  content: string;
  className?: string;
}

export function MarkdownText({ content, className }: Props) {
  return (
    <div className={`md-content ${className ?? ''}`.trim()}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          img: ({ src, alt, ...rest }) => {
            if (src?.startsWith('pending:')) {
              return <span className="pending-img-placeholder">📷 Загрузить рисунок</span>;
            }
            return <img src={src} alt={alt ?? ''} className="md-inline-img" {...rest} />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
