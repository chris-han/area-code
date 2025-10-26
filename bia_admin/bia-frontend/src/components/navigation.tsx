'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  BarChart3,
  Settings,
  Workflow,
  Home,
  ExternalLink,
  DollarSign
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Workflows', href: '/workflows', icon: Workflow },
  { name: 'FinOps', href: '/finops', icon: DollarSign },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Admin', href: '/admin', icon: Settings },
]

const externalLinks = [
  { name: 'Temporal UI', href: process.env.NEXT_PUBLIC_TEMPORAL_UI_URL || 'http://localhost:8080' },
  { name: 'MinIO Console', href: process.env.NEXT_PUBLIC_MINIO_CONSOLE_URL || 'http://localhost:9501' },
  { name: 'Kafdrop', href: process.env.NEXT_PUBLIC_KAFDROP_URL || 'http://localhost:9999' },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-2">
              <BarChart3 className="h-6 w-6 text-primary" />
              <span className="text-xl font-bold">bia Console</span>
            </Link>
            
            <div className="hidden md:flex items-center space-x-1">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                
                return (
                  <Link key={item.name} href={item.href}>
                    <Button
                      variant={isActive ? "default" : "ghost"}
                      size="sm"
                      className="flex items-center space-x-2"
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.name}</span>
                    </Button>
                  </Link>
                )
              })}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="hidden lg:flex items-center space-x-1">
              {externalLinks.map((link) => (
                <Button
                  key={link.name}
                  variant="outline"
                  size="sm"
                  asChild
                >
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1"
                  >
                    <span className="text-xs">{link.name}</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}