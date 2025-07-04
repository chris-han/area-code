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
// Import models from the shared package
import type {
  Foo,
  CreateFoo,
  UpdateFoo,
  Bar,
  CreateBar,
  UpdateBar,
} from "@workspace/models";

// Foo table - matches models package exactly
export const foo = pgTable("foo", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: varchar("name", { length: 255 }).notNull(),
  description: text("description"),
  status: varchar("status", { length: 50 }).notNull().default("active"),
  priority: integer("priority").notNull().default(1),
  isActive: boolean("is_active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

// Bar table - matches models package exactly
export const bar = pgTable("bar", {
  id: uuid("id").primaryKey().defaultRandom(),
  fooId: uuid("foo_id")
    .notNull()
    .references(() => foo.id),
  value: integer("value").notNull(),
  label: varchar("label", { length: 100 }),
  notes: text("notes"),
  isEnabled: boolean("is_enabled").notNull().default(true),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
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
  relationshipType: varchar("relationship_type", { length: 50 }).default(
    "default"
  ),
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

// Export models from shared package for API types
export type { Foo, CreateFoo, UpdateFoo, Bar, CreateBar, UpdateBar };

// Keep Drizzle types for internal database operations
export type DbFoo = typeof foo.$inferSelect;
export type NewDbFoo = typeof foo.$inferInsert;

export type DbBar = typeof bar.$inferSelect;
export type NewDbBar = typeof bar.$inferInsert;

export type FooBar = typeof fooBar.$inferSelect;
export type NewFooBar = typeof fooBar.$inferInsert;
