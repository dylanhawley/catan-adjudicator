'use client';

interface HighlightedTextProps {
  text: string;
  ranges: Array<{ start: number; end: number }>;
  className?: string;
}

const HighlightedText = ({
  text,
  ranges,
  className = '',
}: HighlightedTextProps) => {
  if (ranges.length === 0) {
    return <span className={className}>{text}</span>;
  }

  // Sort ranges by start position
  const sortedRanges = [...ranges].sort((a, b) => a.start - b.start);

  // Build array of text segments with highlights
  const segments: Array<{ text: string; highlighted: boolean }> = [];
  let lastIndex = 0;

  sortedRanges.forEach((range) => {
    // Add text before highlight
    if (range.start > lastIndex) {
      segments.push({
        text: text.slice(lastIndex, range.start),
        highlighted: false,
      });
    }

    // Add highlighted text
    segments.push({
      text: text.slice(range.start, range.end),
      highlighted: true,
    });

    lastIndex = Math.max(lastIndex, range.end);
  });

  // Add remaining text
  if (lastIndex < text.length) {
    segments.push({
      text: text.slice(lastIndex),
      highlighted: false,
    });
  }

  return (
    <span className={className}>
      {segments.map((segment, index) =>
        segment.highlighted ? (
          <mark
            key={index}
            className="bg-yellow-300 text-black"
            aria-label="Highlighted text"
          >
            {segment.text}
          </mark>
        ) : (
          <span key={index}>{segment.text}</span>
        )
      )}
    </span>
  );
};

export default HighlightedText;

