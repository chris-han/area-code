import Fastify from "fastify";
import cors from "@fastify/cors";
import { userRoutes } from "./routes/users";
import { productRoutes } from "./routes/products";
import { orderRoutes } from "./routes/orders";

const fastify = Fastify({
  logger: {
    level: "info",
    prettyPrint: process.env.NODE_ENV === "development",
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
    name: "Transactional Service API",
    version: "1.0.0",
    description:
      "RESTful API for transactional operations with PostgreSQL and Drizzle ORM",
    endpoints: {
      users: "/users",
      products: "/products",
      orders: "/orders",
      health: "/health",
    },
  };
});

// Register route plugins
await fastify.register(userRoutes, { prefix: "/api" });
await fastify.register(productRoutes, { prefix: "/api" });
await fastify.register(orderRoutes, { prefix: "/api" });

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
    const port = parseInt(process.env.PORT || "8080");
    const host = process.env.HOST || "0.0.0.0";

    await fastify.listen({ port, host });

    fastify.log.info(
      `🚀 Transactional service is running on http://${host}:${port}`
    );
    fastify.log.info("📊 Available endpoints:");
    fastify.log.info("  GET  / - API information");
    fastify.log.info("  GET  /health - Health check");
    fastify.log.info("  GET  /api/users - List all users");
    fastify.log.info("  POST /api/users - Create user");
    fastify.log.info("  GET  /api/products - List all products");
    fastify.log.info("  POST /api/products - Create product");
    fastify.log.info("  GET  /api/orders - List all orders");
    fastify.log.info("  POST /api/orders - Create order");
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
