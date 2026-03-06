'use client'

import * as TabsPrimitive from '@radix-ui/react-tabs'
import { cn } from '@/lib/cn'
import { forwardRef, type ComponentPropsWithoutRef } from 'react'

export const Tabs = TabsPrimitive.Root

export const TabsList = forwardRef<
  HTMLDivElement,
  ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      'inline-flex items-center gap-1 border-b border-[var(--border-default)] pb-px',
      className,
    )}
    {...props}
  />
))
TabsList.displayName = 'TabsList'

export const TabsTrigger = forwardRef<
  HTMLButtonElement,
  ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      'inline-flex items-center px-3 py-1.5 text-sm font-medium transition-colors',
      'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
      'border-b-2 border-transparent -mb-px',
      'data-[state=active]:border-brand-500 data-[state=active]:text-brand-600',
      'dark:data-[state=active]:text-brand-400',
      className,
    )}
    {...props}
  />
))
TabsTrigger.displayName = 'TabsTrigger'

export const TabsContent = forwardRef<
  HTMLDivElement,
  ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn('mt-4 focus-visible:outline-none', className)}
    {...props}
  />
))
TabsContent.displayName = 'TabsContent'
