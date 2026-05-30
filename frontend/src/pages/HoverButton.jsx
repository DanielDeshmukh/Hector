import { useState } from 'react'

export default function HoverButton({ children, style, hoverStyle, ...props }) {
  const [hover, setHover] = useState(false)

  return (
    <button
      {...props}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ ...style, ...(hover ? hoverStyle : null) }}
    >
      {children}
    </button>
  )
}
