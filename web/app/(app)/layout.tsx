import { AppLayout } from '@/components/layout/AppLayout'

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AppLayout>{children}</AppLayout>
}
