import {
  pgTable,
  uuid,
  varchar,
  timestamp,
  integer,
  text,
  boolean,
} from "drizzle-orm/pg-core";
import { createInsertSchema, createSelectSchema } from "drizzle-zod";

// Foo table - generic primary entity
export const foo = pgTable("foo", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: varchar("name", { length: 255 }).notNull(),
  description: text("description"),
  status: varchar("status", { length: 50 }).notNull().default("active"),
  priority: integer("priority").default(1),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Bar table - generic secondary entity
export const bar = pgTable("bar", {
  id: uuid("id").primaryKey().defaultRandom(),
  fooId: uuid("foo_id")
    .notNull()
    .references(() => foo.id),
  value: integer("value").notNull(),
  label: varchar("label", { length: 100 }),
  notes: text("notes"),
  isEnabled: boolean("is_enabled").default(true),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// FooBar junction table - many-to-many relationship
export const fooBar = pgTable("foo_bar", {
  id: uuid("id").primaryKey().defaultRandom(),
  fooId: uuid("foo_id")
    .notNull()
    .references(() => foo.id),
  barId: uuid("bar_id")
    .notNull()
    .references(() => bar.id),
  relationshipType: varchar("relationship_type", { length: 50 }).default("default"),
  metadata: text("metadata"), // JSON string for additional data
  createdAt: timestamp("created_at").defaultNow(),
});

// Zod schemas for validation
export const insertFooSchema = createInsertSchema(foo);
export const selectFooSchema = createSelectSchema(foo);

export const insertBarSchema = createInsertSchema(bar);
export const selectBarSchema = createSelectSchema(bar);

export const insertFooBarSchema = createInsertSchema(fooBar);
export const selectFooBarSchema = createSelectSchema(fooBar);

// Types
export type Foo = typeof foo.$inferSelect;
export type NewFoo = typeof foo.$inferInsert;

export type Bar = typeof bar.$inferSelect;
export type NewBar = typeof bar.$inferInsert;

export type FooBar = typeof fooBar.$inferSelect;
export type NewFooBar = typeof fooBar.$inferInsert; 