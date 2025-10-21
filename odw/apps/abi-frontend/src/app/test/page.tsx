import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export default function TestPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Component Test Page</h1>
        <p className="text-muted-foreground">Testing ShadCN UI components and Tailwind CSS</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Button Components</CardTitle>
            <CardDescription>Testing different button variants</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex gap-2 flex-wrap">
              <Button>Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="destructive">Destructive</Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Badge Components</CardTitle>
            <CardDescription>Testing different badge variants</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 flex-wrap">
              <Badge>Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
              <Badge variant="destructive">Destructive</Badge>
              <Badge variant="success">Success</Badge>
              <Badge variant="warning">Warning</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Environment Variables</CardTitle>
          <CardDescription>Testing environment variable loading</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div>API Base URL: <code className="bg-muted px-1 rounded">{process.env.NEXT_PUBLIC_API_BASE_URL}</code></div>
            <div>Temporal UI: <code className="bg-muted px-1 rounded">{process.env.NEXT_PUBLIC_TEMPORAL_UI_URL}</code></div>
            <div>MinIO Console: <code className="bg-muted px-1 rounded">{process.env.NEXT_PUBLIC_MINIO_CONSOLE_URL}</code></div>
            <div>Kafdrop: <code className="bg-muted px-1 rounded">{process.env.NEXT_PUBLIC_KAFDROP_URL}</code></div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}