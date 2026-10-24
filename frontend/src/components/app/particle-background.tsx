import { useEffect, useRef } from 'react'

const LINK_DISTANCE = 140
const POINTER_DISTANCE = 180
const MAX_PARTICLES = 120
const AREA_PER_PARTICLE = 13000

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  r: number
}

const spawn = (width: number, height: number): Particle => ({
  x: Math.random() * width,
  y: Math.random() * height,
  vx: (Math.random() - 0.5) * 0.5,
  vy: (Math.random() - 0.5) * 0.5,
  r: 1 + Math.random() * 1.4,
})

export function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const pointer = { x: -1e4, y: -1e4 }
    const particles: Particle[] = []
    let width = 0
    let height = 0
    let frame = 0

    const line = (ax: number, ay: number, bx: number, by: number, color: string) => {
      ctx.strokeStyle = color
      ctx.beginPath()
      ctx.moveTo(ax, ay)
      ctx.lineTo(bx, by)
      ctx.stroke()
    }

    const draw = () => {
      const dark = document.documentElement.classList.contains('dark')
      const ink = dark ? '255, 255, 255' : '23, 23, 23'
      const linkAlpha = dark ? 0.24 : 0.14

      ctx.clearRect(0, 0, width, height)
      ctx.lineWidth = 0.6

      if (!reduceMotion) {
        for (const p of particles) {
          p.x += p.vx
          p.y += p.vy
          if (p.x < 0 || p.x > width) p.vx *= -1
          if (p.y < 0 || p.y > height) p.vy *= -1
        }
      }

      for (let i = 0; i < particles.length; i++) {
        const a = particles[i]
        for (let j = i + 1; j < particles.length; j++) {
          const b = particles[j]
          const dx = a.x - b.x
          const dy = a.y - b.y
          if (dx * dx + dy * dy >= LINK_DISTANCE * LINK_DISTANCE) continue
          const d = Math.sqrt(dx * dx + dy * dy)
          line(a.x, a.y, b.x, b.y, `rgba(${ink}, ${(1 - d / LINK_DISTANCE) * linkAlpha})`)
        }

        const toPointer = Math.hypot(a.x - pointer.x, a.y - pointer.y)
        if (toPointer < POINTER_DISTANCE) {
          const alpha = (1 - toPointer / POINTER_DISTANCE) * linkAlpha * 1.8
          line(a.x, a.y, pointer.x, pointer.y, `rgba(${ink}, ${alpha})`)
        }

        ctx.fillStyle = `rgba(${ink}, ${dark ? 0.5 : 0.32})`
        ctx.beginPath()
        ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2)
        ctx.fill()
      }

      if (!reduceMotion) frame = requestAnimationFrame(draw)
    }

    // keep particles on resize (mobile URL bar)
    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      width = window.innerWidth
      height = window.innerHeight
      canvas.width = width * dpr
      canvas.height = height * dpr
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      const target = Math.min(MAX_PARTICLES, Math.round((width * height) / AREA_PER_PARTICLE))
      while (particles.length < target) particles.push(spawn(width, height))
      particles.length = target
      for (const p of particles) {
        p.x = Math.min(p.x, width)
        p.y = Math.min(p.y, height)
      }
      if (reduceMotion) draw()
    }

    const onPointerMove = (event: PointerEvent) => {
      pointer.x = event.clientX
      pointer.y = event.clientY
    }
    const onPointerLeave = () => {
      pointer.x = -1e4
      pointer.y = -1e4
    }

    resize()
    if (!reduceMotion) frame = requestAnimationFrame(draw)
    window.addEventListener('resize', resize)
    window.addEventListener('pointermove', onPointerMove, { passive: true })
    document.documentElement.addEventListener('pointerleave', onPointerLeave)

    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', resize)
      window.removeEventListener('pointermove', onPointerMove)
      document.documentElement.removeEventListener('pointerleave', onPointerLeave)
    }
  }, [])

  return <canvas ref={canvasRef} aria-hidden className="pointer-events-none fixed inset-0 -z-10" />
}
