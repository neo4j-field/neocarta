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

-- Insert sample data into customers (25 customers)
INSERT INTO `demo_ecommerce.customers` VALUES
  (1, 'Alice Johnson', 'alice@example.com', TIMESTAMP('2024-01-15 10:30:00')),
  (2, 'Bob Smith', 'bob@example.com', TIMESTAMP('2024-01-16 14:20:00')),
  (3, 'Carol Williams', 'carol@example.com', TIMESTAMP('2024-01-18 09:15:00')),
  (4, 'David Brown', 'david@example.com', TIMESTAMP('2024-01-20 16:45:00')),
  (5, 'Emma Davis', 'emma@example.com', TIMESTAMP('2024-01-22 11:30:00')),
  (6, 'Frank Miller', 'frank@example.com', TIMESTAMP('2024-01-25 13:00:00')),
  (7, 'Grace Wilson', 'grace@example.com', TIMESTAMP('2024-01-28 10:20:00')),
  (8, 'Henry Moore', 'henry@example.com', TIMESTAMP('2024-02-01 15:30:00')),
  (9, 'Ivy Taylor', 'ivy@example.com', TIMESTAMP('2024-02-03 09:45:00')),
  (10, 'Jack Anderson', 'jack@example.com', TIMESTAMP('2024-02-05 14:10:00')),
  (11, 'Kelly Thomas', 'kelly@example.com', TIMESTAMP('2024-02-08 11:50:00')),
  (12, 'Liam Jackson', 'liam@example.com', TIMESTAMP('2024-02-10 16:20:00')),
  (13, 'Mia White', 'mia@example.com', TIMESTAMP('2024-02-12 10:00:00')),
  (14, 'Noah Harris', 'noah@example.com', TIMESTAMP('2024-02-15 13:40:00')),
  (15, 'Olivia Martin', 'olivia@example.com', TIMESTAMP('2024-02-18 09:30:00')),
  (16, 'Peter Thompson', 'peter@example.com', TIMESTAMP('2024-02-20 15:15:00')),
  (17, 'Quinn Garcia', 'quinn@example.com', TIMESTAMP('2024-02-22 11:25:00')),
  (18, 'Rachel Martinez', 'rachel@example.com', TIMESTAMP('2024-02-25 14:50:00')),
  (19, 'Sam Robinson', 'sam@example.com', TIMESTAMP('2024-02-28 10:40:00')),
  (20, 'Tina Clark', 'tina@example.com', TIMESTAMP('2024-03-02 16:00:00')),
  (21, 'Uma Rodriguez', 'uma@example.com', TIMESTAMP('2024-03-05 12:30:00')),
  (22, 'Victor Lewis', 'victor@example.com', TIMESTAMP('2024-03-08 09:20:00')),
  (23, 'Wendy Lee', 'wendy@example.com', TIMESTAMP('2024-03-10 15:45:00')),
  (24, 'Xavier Walker', 'xavier@example.com', TIMESTAMP('2024-03-12 11:10:00')),
  (25, 'Yara Hall', 'yara@example.com', TIMESTAMP('2024-03-15 14:25:00'));

-- Insert sample data into products (25 products)
INSERT INTO `demo_ecommerce.products` VALUES
  (101, 'Laptop', 'Electronics', 999.99),
  (102, 'Mouse', 'Electronics', 29.99),
  (103, 'Keyboard', 'Electronics', 79.99),
  (104, 'Monitor', 'Electronics', 299.99),
  (105, 'Webcam', 'Electronics', 89.99),
  (106, 'Headphones', 'Electronics', 149.99),
  (107, 'USB Cable', 'Electronics', 9.99),
  (108, 'External Hard Drive', 'Electronics', 119.99),
  (109, 'Desk Lamp', 'Home & Office', 39.99),
  (110, 'Office Chair', 'Home & Office', 249.99),
  (111, 'Standing Desk', 'Home & Office', 399.99),
  (112, 'Notebook', 'Home & Office', 5.99),
  (113, 'Pen Set', 'Home & Office', 12.99),
  (114, 'T-Shirt', 'Clothing', 19.99),
  (115, 'Jeans', 'Clothing', 59.99),
  (116, 'Sneakers', 'Clothing', 89.99),
  (117, 'Jacket', 'Clothing', 129.99),
  (118, 'Backpack', 'Clothing', 49.99),
  (119, 'Water Bottle', 'Sports', 14.99),
  (120, 'Yoga Mat', 'Sports', 29.99),
  (121, 'Dumbbells', 'Sports', 79.99),
  (122, 'Running Shoes', 'Sports', 119.99),
  (123, 'Fitness Tracker', 'Sports', 99.99),
  (124, 'Protein Powder', 'Sports', 39.99),
  (125, 'Resistance Bands', 'Sports', 24.99);

-- Insert sample data into orders (30 orders)
INSERT INTO `demo_ecommerce.orders` VALUES
  (1001, 1, TIMESTAMP('2024-01-20 11:00:00'), 1029.98),
  (1002, 2, TIMESTAMP('2024-01-21 15:30:00'), 79.99),
  (1003, 3, TIMESTAMP('2024-01-23 10:15:00'), 299.99),
  (1004, 4, TIMESTAMP('2024-01-25 14:45:00'), 449.97),
  (1005, 5, TIMESTAMP('2024-01-28 09:30:00'), 159.98),
  (1006, 1, TIMESTAMP('2024-02-02 16:20:00'), 649.98),
  (1007, 6, TIMESTAMP('2024-02-05 11:50:00'), 89.99),
  (1008, 7, TIMESTAMP('2024-02-08 13:15:00'), 249.99),
  (1009, 8, TIMESTAMP('2024-02-10 10:40:00'), 399.99),
  (1010, 9, TIMESTAMP('2024-02-12 15:00:00'), 44.98),
  (1011, 10, TIMESTAMP('2024-02-15 09:25:00'), 179.97),
  (1012, 11, TIMESTAMP('2024-02-18 14:30:00'), 129.99),
  (1013, 12, TIMESTAMP('2024-02-20 11:10:00'), 299.97),
  (1014, 13, TIMESTAMP('2024-02-22 16:45:00'), 49.99),
  (1015, 14, TIMESTAMP('2024-02-25 10:20:00'), 209.97),
  (1016, 15, TIMESTAMP('2024-02-28 13:50:00'), 119.99),
  (1017, 16, TIMESTAMP('2024-03-02 09:15:00'), 154.98),
  (1018, 17, TIMESTAMP('2024-03-05 15:40:00'), 399.99),
  (1019, 18, TIMESTAMP('2024-03-08 11:30:00'), 229.98),
  (1020, 19, TIMESTAMP('2024-03-10 14:05:00'), 64.98),
  (1021, 20, TIMESTAMP('2024-03-12 10:50:00'), 119.99),
  (1022, 21, TIMESTAMP('2024-03-15 16:25:00'), 179.98),
  (1023, 22, TIMESTAMP('2024-03-18 09:40:00'), 89.99),
  (1024, 23, TIMESTAMP('2024-03-20 13:20:00'), 349.98),
  (1025, 24, TIMESTAMP('2024-03-22 11:55:00'), 99.99),
  (1026, 25, TIMESTAMP('2024-03-25 15:10:00'), 199.98),
  (1027, 3, TIMESTAMP('2024-03-28 10:30:00'), 529.98),
  (1028, 7, TIMESTAMP('2024-03-30 14:00:00'), 139.98),
  (1029, 12, TIMESTAMP('2024-04-02 09:45:00'), 289.97),
  (1030, 18, TIMESTAMP('2024-04-05 16:15:00'), 449.97);

-- Insert sample data into order_items (60+ order items)
INSERT INTO `demo_ecommerce.order_items` VALUES
  (10001, 1001, 101, 1, 999.99),
  (10002, 1001, 102, 1, 29.99),
  (10003, 1002, 103, 1, 79.99),
  (10004, 1003, 104, 1, 299.99),
  (10005, 1004, 111, 1, 399.99),
  (10006, 1004, 112, 1, 5.99),
  (10007, 1004, 113, 1, 12.99),
  (10008, 1004, 109, 1, 39.99),
  (10009, 1005, 106, 1, 149.99),
  (10010, 1005, 107, 1, 9.99),
  (10011, 1006, 110, 1, 249.99),
  (10012, 1006, 111, 1, 399.99),
  (10013, 1007, 105, 1, 89.99),
  (10014, 1008, 110, 1, 249.99),
  (10015, 1009, 111, 1, 399.99),
  (10016, 1010, 119, 2, 14.99),
  (10017, 1010, 112, 1, 5.99),
  (10018, 1010, 113, 2, 12.99),
  (10019, 1011, 114, 3, 19.99),
  (10020, 1011, 115, 2, 59.99),
  (10021, 1012, 117, 1, 129.99),
  (10022, 1013, 104, 1, 299.99),
  (10023, 1014, 118, 1, 49.99),
  (10024, 1015, 116, 1, 89.99),
  (10025, 1015, 115, 2, 59.99),
  (10026, 1016, 122, 1, 119.99),
  (10027, 1017, 120, 2, 29.99),
  (10028, 1017, 121, 1, 79.99),
  (10029, 1017, 112, 3, 5.99),
  (10030, 1018, 111, 1, 399.99),
  (10031, 1019, 123, 1, 99.99),
  (10032, 1019, 124, 2, 39.99),
  (10033, 1019, 118, 1, 49.99),
  (10034, 1020, 125, 2, 24.99),
  (10035, 1020, 119, 1, 14.99),
  (10036, 1021, 122, 1, 119.99),
  (10037, 1022, 101, 1, 999.99),
  (10038, 1022, 102, 1, 29.99),
  (10039, 1022, 103, 1, 79.99),
  (10040, 1022, 107, 3, 9.99),
  (10041, 1023, 105, 1, 89.99),
  (10042, 1024, 108, 2, 119.99),
  (10043, 1024, 106, 1, 149.99),
  (10044, 1025, 123, 1, 99.99),
  (10045, 1026, 104, 1, 299.99),
  (10046, 1026, 102, 2, 29.99),
  (10047, 1026, 103, 1, 79.99),
  (10048, 1027, 110, 1, 249.99),
  (10049, 1027, 109, 2, 39.99),
  (10050, 1027, 112, 5, 5.99),
  (10051, 1027, 113, 3, 12.99),
  (10052, 1028, 114, 3, 19.99),
  (10053, 1028, 115, 1, 59.99),
  (10054, 1029, 117, 1, 129.99),
  (10055, 1029, 116, 1, 89.99),
  (10056, 1029, 118, 1, 49.99),
  (10057, 1029, 119, 2, 14.99),
  (10058, 1030, 121, 2, 79.99),
  (10059, 1030, 120, 3, 29.99),
  (10060, 1030, 125, 4, 24.99),
  (10061, 1030, 124, 2, 39.99);
