import { createFileRoute } from '@tanstack/react-router'
import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card";
import { Link } from '@tanstack/react-router'

function Index() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">shadcn/ui Monorepo with TanStack Router</CardTitle>
          <CardDescription>
            Successfully configured with monorepo best practices and routing!
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center space-y-2">
            <p className="text-sm text-muted-foreground">
              Components are shared from @workspace/ui
            </p>
            <div className="flex flex-col space-y-2">
              <Button>Default Button</Button>
              <Button variant="outline">Outline Button</Button>
              <Button variant="destructive">Destructive Button</Button>
            </div>
          </div>
          <div className="border-t pt-4">
            <p className="text-sm text-muted-foreground mb-2 text-center">
              Try out TanStack Form:
            </p>
            <Link to="/form-example">
              <Button variant="outline" className="w-full">
                View Form Example
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export const Route = createFileRoute('/')({
  component: Index,
}) 