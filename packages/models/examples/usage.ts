import { 
  type Foo, 
  type CreateFoo, 
  type Bar, 
  type CreateBar,
  FooStatus,
  createFooThingEvent,
  createBarThingEvent,
  isFooThingEvent,
  isBarThingEvent,
  type Event
} from '../src/index';

// Example: Creating a new Foo with type safety
const newFooData: CreateFoo = {
  name: "Example Foo",
  description: "This is an example foo item",
  status: FooStatus.ACTIVE,
  priority: 5,
  isActive: true
};

console.log("✅ Foo data created:", newFooData);

// Example: Creating a new Bar with type safety
const newBarData: CreateBar = {
  fooId: "123e4567-e89b-12d3-a456-426614174000",
  value: 42,
  label: "Example Bar",
  notes: "This is an example bar item",
  isEnabled: true
};

console.log("✅ Bar data created:", newBarData);

// Example: Type-safe foo processing
const processFoo = (foo: Foo) => {
  console.log(`Processing foo: ${foo.name} (ID: ${foo.id})`);
  console.log(`Status: ${foo.status}, Priority: ${foo.priority}`);
  if (foo.description) {
    console.log(`Description: ${foo.description}`);
  }
};

// Example: Type-safe bar processing
const processBar = (bar: Bar) => {
  console.log(`Processing bar: ${bar.label || 'Unlabeled'} (ID: ${bar.id})`);
  console.log(`Value: ${bar.value}, Foo ID: ${bar.fooId}`);
  console.log(`Enabled: ${bar.isEnabled}`);
};

// Example: Creating events with factory functions
const fooEvent = createFooThingEvent({
  fooId: "123e4567-e89b-12d3-a456-426614174000",
  action: "created",
  currentData: newFooData
}, {
  source: "api",
  correlationId: "123e4567-e89b-12d3-a456-426614174002"
});

const barEvent = createBarThingEvent({
  barId: "123e4567-e89b-12d3-a456-426614174001",
  fooId: "123e4567-e89b-12d3-a456-426614174000",
  action: "created",
  currentData: newBarData,
  value: 42
});

console.log("🎉 FooThing Event:", fooEvent);
console.log("🎉 BarThing Event:", barEvent);

// Example: Type guards usage with type safety
const processEvent = (event: Event) => {
  if (isFooThingEvent(event)) {
    // TypeScript knows this is a FooThingEvent
    console.log(`Processing foo event: ${event.params.action} for foo ${event.params.fooId}`);
    console.log(`Event ID: ${event.id}, Source: ${event.source}`);
  } else if (isBarThingEvent(event)) {
    // TypeScript knows this is a BarThingEvent
    console.log(`Processing bar event: ${event.params.action} for bar ${event.params.barId} (foo: ${event.params.fooId})`);
    if (event.params.value !== undefined) {
      console.log(`Bar value: ${event.params.value}`);
    }
  }
};

processEvent(fooEvent);
processEvent(barEvent);

// Example: Type checking at compile time
const validateFooData = (data: unknown): data is CreateFoo => {
  return (
    typeof data === 'object' &&
    data !== null &&
    'name' in data &&
    typeof (data as any).name === 'string'
  );
};

// Usage of type guard
const someData: unknown = {
  name: "Test Foo",
  description: "A test foo item"
};

if (validateFooData(someData)) {
  // TypeScript now knows someData is CreateFoo
  console.log(`Validated foo name: ${someData.name}`);
} 