-- Create dataset with description
CREATE SCHEMA IF NOT EXISTS `demo_ecommerce`
OPTIONS(
  description="Demo e-commerce dataset with foreign key relationships for testing"
);

-- 1. Customers table
CREATE OR REPLACE TABLE `demo_ecommerce.customers` (
  customer_id INT64 OPTIONS(description="Unique identifier for the customer"),
  customer_name STRING OPTIONS(description="Full name of the customer"),
  email STRING OPTIONS(description="Customer's email address"),
  created_at TIMESTAMP OPTIONS(description="Timestamp when the customer record was created"),
  PRIMARY KEY (customer_id) NOT ENFORCED
)
OPTIONS(
  description="Customer master table containing all registered customers"
);

-- 2. Products table
CREATE OR REPLACE TABLE `demo_ecommerce.products` (
  product_id INT64 OPTIONS(description="Unique identifier for the product"),
  product_name STRING OPTIONS(description="Name of the product"),
  category STRING OPTIONS(description="Product category (e.g., Electronics, Clothing)"),
  price NUMERIC OPTIONS(description="Product price in USD"),
  PRIMARY KEY (product_id) NOT ENFORCED
)
OPTIONS(
  description="Product catalog containing all available products"
);

-- 3. Orders table (with foreign key to customers)
CREATE OR REPLACE TABLE `demo_ecommerce.orders` (
  order_id INT64 OPTIONS(description="Unique identifier for the order"),
  customer_id INT64 OPTIONS(description="Foreign key reference to customers table"),
  order_date TIMESTAMP OPTIONS(description="Timestamp when the order was placed"),
  total_amount NUMERIC OPTIONS(description="Total order amount in USD"),
  PRIMARY KEY (order_id) NOT ENFORCED,
  CONSTRAINT fk_customer FOREIGN KEY (customer_id) 
    REFERENCES `demo_ecommerce.customers` (customer_id) NOT ENFORCED
)
OPTIONS(
  description="Orders placed by customers, links to customers via customer_id foreign key"
);

-- 4. Order items table (with foreign keys to orders and products)
CREATE OR REPLACE TABLE `demo_ecommerce.order_items` (
  order_item_id INT64 OPTIONS(description="Unique identifier for the order line item"),
  order_id INT64 OPTIONS(description="Foreign key reference to orders table"),
  product_id INT64 OPTIONS(description="Foreign key reference to products table"),
  quantity INT64 OPTIONS(description="Quantity of the product ordered"),
  price NUMERIC OPTIONS(description="Price per unit at time of order in USD"),
  PRIMARY KEY (order_item_id) NOT ENFORCED,
  CONSTRAINT fk_order FOREIGN KEY (order_id) 
    REFERENCES `demo_ecommerce.orders` (order_id) NOT ENFORCED,
  CONSTRAINT fk_product FOREIGN KEY (product_id) 
    REFERENCES `demo_ecommerce.products` (product_id) NOT ENFORCED
)
OPTIONS(
  description="Individual line items for each order, links to orders and products via foreign keys"
);

-- Insert sample data into customers
INSERT INTO `demo_ecommerce.customers` VALUES
  (1, 'Alice Johnson', 'alice@example.com', CURRENT_TIMESTAMP()),
  (2, 'Bob Smith', 'bob@example.com', CURRENT_TIMESTAMP());

-- Insert sample data into products
INSERT INTO `demo_ecommerce.products` VALUES
  (101, 'Laptop', 'Electronics', 999.99),
  (102, 'Mouse', 'Electronics', 29.99),
  (103, 'Keyboard', 'Electronics', 79.99);

-- Insert sample data into orders
INSERT INTO `demo_ecommerce.orders` VALUES
  (1001, 1, CURRENT_TIMESTAMP(), 1029.98),
  (1002, 2, CURRENT_TIMESTAMP(), 79.99);

-- Insert sample data into order_items
INSERT INTO `demo_ecommerce.order_items` VALUES
  (10001, 1001, 101, 1, 999.99),
  (10002, 1001, 102, 1, 29.99),
  (10003, 1002, 103, 1, 79.99);
