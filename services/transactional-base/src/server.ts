import Fastify from "fastify";
import cors from "@fastify/cors";
import { fooRoutes } from "./routes/foo";
import { barRoutes } from "./routes/bar";
import { fooBarRoutes } from "./routes/fooBar";

const fastify = Fastify({
  logger: {
    level: "info",
    transport:
      process.env.NODE_ENV === "development"
        ? { target: "pino-pretty" }
        : undefined,
  },
});

// Register CORS
await fastify.register(cors, {
  origin: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
});

// Health check route
fastify.get("/health", async (request, reply) => {
  return { status: "ok", timestamp: new Date().toISOString() };
});

// API info route
fastify.get("/", async (request, reply) => {
  return {
    name: "Transactional Base Service API",
    version: "1.0.0",
    description:
      "RESTful API for generic transactional operations with foo and bar entities using PostgreSQL and Drizzle ORM",
    endpoints: {
      foo: "/foo",
      bar: "/bar",
      "foo-bar": "/foo-bar",
      health: "/health",
    },
  };
});

// Register route plugins
await fastify.register(fooRoutes, { prefix: "/api" });
await fastify.register(barRoutes, { prefix: "/api" });
await fastify.register(fooBarRoutes, { prefix: "/api" });

// Error handler
fastify.setErrorHandler((error, request, reply) => {
  fastify.log.error(error);

  if (error.validation) {
    reply.status(400).send({
      error: "Validation Error",
      message: error.message,
      details: error.validation,
    });
    return;
  }

  reply.status(500).send({
    error: "Internal Server Error",
    message: "Something went wrong",
  });
});

// Start server
const start = async () => {
  try {
    const port = parseInt(process.env.PORT || "8081");
    const host = process.env.HOST || "0.0.0.0";

    await fastify.listen({ port, host });

    fastify.log.info(
      `🚀 Transactional Base service is running on http://${host}:${port}`
    );
    fastify.log.info("📊 Available endpoints:");
    fastify.log.info("  GET  / - API information");
    fastify.log.info("  GET  /health - Health check");
    fastify.log.info("  GET  /api/foo - List all foo items");
    fastify.log.info("  POST /api/foo - Create foo item");
    fastify.log.info("  GET  /api/bar - List all bar items");
    fastify.log.info("  POST /api/bar - Create bar item");
    fastify.log.info("  GET  /api/foo-bar - List all foo-bar relationships");
    fastify.log.info("  POST /api/foo-bar - Create foo-bar relationship");
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start(); 