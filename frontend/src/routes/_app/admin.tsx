import { AdminSettings } from '@/components/admin/AdminSettings'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_app/admin')({
  component: () => <AdminSettings />
})
