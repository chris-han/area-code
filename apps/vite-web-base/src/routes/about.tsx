import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from "@workspace/ui/components/card";

function About() {
  const { isPending, error, data } = useQuery({
    queryKey: ['repoData'],
    queryFn: () =>
      fetch('https://api.github.com/repos/TanStack/query').then((res) =>
        res.json(),
      ),
  })

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="space-y-6 w-full max-w-2xl">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-xl">About Page with TanStack Query</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-center text-muted-foreground mb-4">
              This page demonstrates TanStack Query fetching GitHub repository data!
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">TanStack Query Repository Stats</CardTitle>
          </CardHeader>
          <CardContent>
            {isPending && (
              <div className="text-center py-4">
                <p>Loading repository data...</p>
              </div>
            )}

            {error && (
              <div className="text-center py-4 text-destructive">
                <p>An error occurred: {error.message}</p>
              </div>
            )}

            {data && (
              <div className="space-y-2">
                <h3 className="text-xl font-semibold">{data.name}</h3>
                <p className="text-muted-foreground">{data.description}</p>
                <div className="flex gap-4 mt-4">
                  <span className="flex items-center gap-1">
                    <strong>👀 {data.subscribers_count}</strong>
                    <span className="text-sm text-muted-foreground">watchers</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <strong>✨ {data.stargazers_count}</strong>
                    <span className="text-sm text-muted-foreground">stars</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <strong>🍴 {data.forks_count}</strong>
                    <span className="text-sm text-muted-foreground">forks</span>
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export const Route = createFileRoute('/about')({
  component: About,
}) 