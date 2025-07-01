// Foo data model interfaces
export interface Foo {
  id: string;
  name: string;
  description?: string;
  status: string;
  priority: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Interface for creating new foo (without generated fields)
export interface CreateFoo {
  name: string;
  description?: string;
  status?: string;
  priority?: number;
  isActive?: boolean;
}

// Interface for updating foo (all fields optional except id)
export interface UpdateFoo {
  id: string;
  name?: string;
  description?: string;
  status?: string;
  priority?: number;
  isActive?: boolean;
  updatedAt?: Date;
}

// Status enum for better type safety
export const FooStatus = {
  ACTIVE: "active",
  INACTIVE: "inactive",
  PENDING: "pending",
  ARCHIVED: "archived",
} as const;

export type FooStatusType = typeof FooStatus[keyof typeof FooStatus]; 