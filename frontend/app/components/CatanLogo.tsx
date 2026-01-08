interface CatanLogoProps {
  size?: number;
  className?: string;
}

export default function CatanLogo({ size = 32, className = '' }: CatanLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Hexagon */}
      <path
        d="M20 2L36.6 11V29L20 38L3.4 29V11L20 2Z"
        stroke="#37352f"
        strokeWidth="2"
        fill="#faf9f7"
      />
      {/* Simple house/settlement */}
      <path
        d="M20 12L28 18V28H12V18L20 12Z"
        fill="#c4694a"
      />
      {/* Roof accent */}
      <path
        d="M20 12L28 18H12L20 12Z"
        fill="#b35a3d"
      />
    </svg>
  );
}
