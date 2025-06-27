import { createFileRoute } from '@tanstack/react-router'
import { useForm } from '@tanstack/react-form'
import { Button } from "@workspace/ui/components/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { useState } from 'react'

interface FormData {
  firstName: string
  lastName: string
  email: string
  age: number
  message: string
}

function FormExample() {
  const [submittedData, setSubmittedData] = useState<FormData | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm({
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
      age: 0,
      message: '',
    },
    onSubmit: async ({ value }) => {
      setIsSubmitting(true)
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      setSubmittedData(value)
      setIsSubmitting(false)
      console.log('Form submitted:', value)
    },
  })

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-6">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">TanStack Form Example</CardTitle>
            <CardDescription>
              A comprehensive form example with validation and state management
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                e.stopPropagation()
                form.handleSubmit()
              }}
              className="space-y-4"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <form.Field
                  name="firstName"
                  validators={{
                    onChange: ({ value }) =>
                      !value ? 'First name is required' : undefined,
                    onChangeAsyncDebounceMs: 500,
                    onChangeAsync: async ({ value }) => {
                      await new Promise((resolve) => setTimeout(resolve, 1000))
                      return value.includes('error') ? 'No "error" allowed in first name' : undefined
                    },
                  }}
                  children={(field) => (
                    <div>
                      <label htmlFor={field.name} className="block text-sm font-medium mb-1">
                        First Name *
                      </label>
                      <input
                        id={field.name}
                        name={field.name}
                        value={field.state.value}
                        onBlur={field.handleBlur}
                        onChange={(e) => field.handleChange(e.target.value)}
                        className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                        placeholder="Enter your first name"
                      />
                      {field.state.meta.isTouched && field.state.meta.errors.length ? (
                        <p className="text-sm text-destructive mt-1">
                          {field.state.meta.errors[0]}
                        </p>
                      ) : null}
                    </div>
                  )}
                />

                <form.Field
                  name="lastName"
                  validators={{
                    onChange: ({ value }) =>
                      !value ? 'Last name is required' : undefined,
                  }}
                  children={(field) => (
                    <div>
                      <label htmlFor={field.name} className="block text-sm font-medium mb-1">
                        Last Name *
                      </label>
                      <input
                        id={field.name}
                        name={field.name}
                        value={field.state.value}
                        onBlur={field.handleBlur}
                        onChange={(e) => field.handleChange(e.target.value)}
                        className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                        placeholder="Enter your last name"
                      />
                      {field.state.meta.isTouched && field.state.meta.errors.length ? (
                        <p className="text-sm text-destructive mt-1">
                          {field.state.meta.errors[0]}
                        </p>
                      ) : null}
                    </div>
                  )}
                />
              </div>

              <form.Field
                name="email"
                validators={{
                  onChange: ({ value }) => {
                    if (!value) return 'Email is required'
                    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                      return 'Please enter a valid email address'
                    }
                    return undefined
                  },
                }}
                children={(field) => (
                  <div>
                    <label htmlFor={field.name} className="block text-sm font-medium mb-1">
                      Email Address *
                    </label>
                    <input
                      id={field.name}
                      name={field.name}
                      type="email"
                      value={field.state.value}
                      onBlur={field.handleBlur}
                      onChange={(e) => field.handleChange(e.target.value)}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                      placeholder="Enter your email"
                    />
                    {field.state.meta.isTouched && field.state.meta.errors.length ? (
                      <p className="text-sm text-destructive mt-1">
                        {field.state.meta.errors[0]}
                      </p>
                    ) : null}
                  </div>
                )}
              />

              <form.Field
                name="age"
                validators={{
                  onChange: ({ value }) => {
                    if (value < 18) return 'Must be 18 or older'
                    if (value > 120) return 'Age must be realistic'
                    return undefined
                  },
                }}
                children={(field) => (
                  <div>
                    <label htmlFor={field.name} className="block text-sm font-medium mb-1">
                      Age
                    </label>
                    <input
                      id={field.name}
                      name={field.name}
                      type="number"
                      value={field.state.value}
                      onBlur={field.handleBlur}
                      onChange={(e) => field.handleChange(Number(e.target.value))}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                      placeholder="Enter your age"
                    />
                    {field.state.meta.isTouched && field.state.meta.errors.length ? (
                      <p className="text-sm text-destructive mt-1">
                        {field.state.meta.errors[0]}
                      </p>
                    ) : null}
                  </div>
                )}
              />

              <form.Field
                name="message"
                validators={{
                  onChange: ({ value }) =>
                    value.length < 10 ? 'Message must be at least 10 characters' : undefined,
                }}
                children={(field) => (
                  <div>
                    <label htmlFor={field.name} className="block text-sm font-medium mb-1">
                      Message
                    </label>
                    <textarea
                      id={field.name}
                      name={field.name}
                      value={field.state.value}
                      onBlur={field.handleBlur}
                      onChange={(e) => field.handleChange(e.target.value)}
                      rows={4}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
                      placeholder="Enter your message (min 10 characters)"
                    />
                    <div className="flex justify-between items-center mt-1">
                      {field.state.meta.isTouched && field.state.meta.errors.length ? (
                        <p className="text-sm text-destructive">
                          {field.state.meta.errors[0]}
                        </p>
                      ) : <span />}
                      <p className="text-xs text-muted-foreground">
                        {field.state.value.length}/500
                      </p>
                    </div>
                  </div>
                )}
              />

              <div className="flex gap-4">
                <form.Subscribe
                  selector={(state) => [state.canSubmit, state.isSubmitting]}
                  children={([canSubmit, isSubmitting]) => (
                    <Button
                      type="submit"
                      disabled={!canSubmit}
                      className="flex-1"
                    >
                      {isSubmitting ? 'Submitting...' : 'Submit Form'}
                    </Button>
                  )}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => form.reset()}
                  className="flex-1"
                >
                  Reset Form
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {submittedData && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg text-green-600">Form Submitted Successfully!</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted p-4 rounded-md text-sm overflow-auto">
                {JSON.stringify(submittedData, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export const Route = createFileRoute('/form-example')({
  component: FormExample,
}) 