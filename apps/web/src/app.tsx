import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card";

function App() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">shadcn/ui Monorepo</CardTitle>
          <CardDescription>
            Successfully configured with monorepo best practices!
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
        </CardContent>
      </Card>
    </div>
  );
}

export default App;
