import { FastifyInstance } from "fastify";
import { eq, and } from "drizzle-orm";
import { db } from "../database/connection";
import {
  fooBar,
  foo,
  bar,
  insertFooBarSchema,
  type FooBar,
  type NewFooBar,
} from "../database/schema";

export async function fooBarRoutes(fastify: FastifyInstance) {
  // Get all foo-bar relationships with details
  fastify.get<{ Reply: any[] | { error: string } }>(
    "/foo-bar",
    async (request, reply) => {
      try {
        const allFooBar = await db
          .select({
            id: fooBar.id,
            relationshipType: fooBar.relationshipType,
            metadata: fooBar.metadata,
            createdAt: fooBar.createdAt,
            foo: {
              id: foo.id,
              name: foo.name,
              status: foo.status,
            },
            bar: {
              id: bar.id,
              label: bar.label,
              value: bar.value,
            },
          })
          .from(fooBar)
          .leftJoin(foo, eq(fooBar.fooId, foo.id))
          .leftJoin(bar, eq(fooBar.barId, bar.id));

        return reply.send(allFooBar);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch foo-bar relationships" });
      }
    }
  );

  // Create new foo-bar relationship
  fastify.post<{ Body: NewFooBar; Reply: FooBar | { error: string } }>(
    "/foo-bar",
    async (request, reply) => {
      try {
        const validatedData = insertFooBarSchema.parse(request.body);

        // Verify that both foo and bar exist
        const fooExists = await db
          .select()
          .from(foo)
          .where(eq(foo.id, validatedData.fooId))
          .limit(1);

        const barExists = await db
          .select()
          .from(bar)
          .where(eq(bar.id, validatedData.barId))
          .limit(1);

        if (fooExists.length === 0) {
          return reply.status(400).send({ error: "Referenced foo does not exist" });
        }

        if (barExists.length === 0) {
          return reply.status(400).send({ error: "Referenced bar does not exist" });
        }

        // Check if relationship already exists
        const existingRelation = await db
          .select()
          .from(fooBar)
          .where(
            and(
              eq(fooBar.fooId, validatedData.fooId),
              eq(fooBar.barId, validatedData.barId)
            )
          )
          .limit(1);

        if (existingRelation.length > 0) {
          return reply.status(400).send({ error: "Relationship already exists" });
        }

        const newFooBar = await db
          .insert(fooBar)
          .values(validatedData)
          .returning();

        return reply.status(201).send(newFooBar[0]);
      } catch (error) {
        return reply.status(400).send({ error: "Invalid foo-bar relationship data" });
      }
    }
  );

  // Delete foo-bar relationship
  fastify.delete<{
    Params: { id: string };
    Reply: { success: boolean } | { error: string };
  }>("/foo-bar/:id", async (request, reply) => {
    try {
      const { id } = request.params;
      const deletedFooBar = await db
        .delete(fooBar)
        .where(eq(fooBar.id, id))
        .returning();

      if (deletedFooBar.length === 0) {
        return reply.status(404).send({ error: "Foo-bar relationship not found" });
      }

      return reply.send({ success: true });
    } catch (error) {
      return reply.status(500).send({ error: "Failed to delete foo-bar relationship" });
    }
  });

  // Get relationships by foo ID
  fastify.get<{ Params: { fooId: string }; Reply: any[] | { error: string } }>(
    "/foo/:fooId/relationships",
    async (request, reply) => {
      try {
        const { fooId } = request.params;
        const relationships = await db
          .select({
            id: fooBar.id,
            relationshipType: fooBar.relationshipType,
            metadata: fooBar.metadata,
            createdAt: fooBar.createdAt,
            bar: {
              id: bar.id,
              label: bar.label,
              value: bar.value,
              notes: bar.notes,
            },
          })
          .from(fooBar)
          .leftJoin(bar, eq(fooBar.barId, bar.id))
          .where(eq(fooBar.fooId, fooId));

        return reply.send(relationships);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch relationships for foo" });
      }
    }
  );

  // Get relationships by bar ID
  fastify.get<{ Params: { barId: string }; Reply: any[] | { error: string } }>(
    "/bar/:barId/relationships",
    async (request, reply) => {
      try {
        const { barId } = request.params;
        const relationships = await db
          .select({
            id: fooBar.id,
            relationshipType: fooBar.relationshipType,
            metadata: fooBar.metadata,
            createdAt: fooBar.createdAt,
            foo: {
              id: foo.id,
              name: foo.name,
              description: foo.description,
              status: foo.status,
            },
          })
          .from(fooBar)
          .leftJoin(foo, eq(fooBar.fooId, foo.id))
          .where(eq(fooBar.barId, barId));

        return reply.send(relationships);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch relationships for bar" });
      }
    }
  );
} 