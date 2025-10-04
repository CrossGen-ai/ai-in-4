import { Layout } from './components/layout/Layout';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';

function App() {
  return (
    <Layout>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Welcome</CardTitle>
            <CardDescription>
              React + TypeScript + Tailwind v4 + Shadcn + FastAPI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => alert('Hello!')}>
              Click me
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}

export default App;
