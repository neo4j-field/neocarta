"""Question bank with evaluation samples for the ecommerce dataset."""

from eval.datasets.models import EvalSample


def get_ecommerce_eval_samples() -> list[EvalSample]:
    """
    Get 10 evaluation samples covering different archetypes.

    Based on the demo_ecommerce dataset with tables:
    - customers (customer_id, customer_name, email, created_at)
    - products (product_id, product_name, category, price)
    - orders (order_id, customer_id, order_date, total_amount)
    - order_items (order_item_id, order_id, product_id, quantity, price)

    Returns
    -------
    list[EvalSample]
        List of 10 evaluation samples
    """
    return [
        # 1. simple_lookup - Single table query
        EvalSample(
            question_id="q001",
            archetype="simple_lookup",
            nl_question="How many customers do we have?",
            ground_truth_sql="""
SELECT COUNT(*) as customer_count
FROM `demo_ecommerce.customers`
            """.strip(),
            required_objects={
                "tables": {"demo_ecommerce.customers", "customers"},
                "columns": set(),  # COUNT(*) doesn't require specific columns
                "joins": set(),
            },
        ),

        # 2. simple_lookup - Single table with filter
        EvalSample(
            question_id="q002",
            archetype="simple_lookup",
            nl_question="List all products in the Electronics category",
            ground_truth_sql="""
SELECT product_name
FROM `demo_ecommerce.products`
WHERE category = 'Electronics'
            """.strip(),
            required_objects={
                "tables": {"demo_ecommerce.products", "products"},
                "columns": {"product_name", "category"},
                "joins": set(),
            },
        ),

        # 3. implicit_join - Two table join
        EvalSample(
            question_id="q003",
            archetype="implicit_join",
            nl_question="Show me all orders placed by Alice Johnson",
            ground_truth_sql="""
SELECT o.order_id, o.order_date, o.total_amount
FROM `demo_ecommerce.orders` o
JOIN `demo_ecommerce.customers` c ON o.customer_id = c.customer_id
WHERE c.customer_name = 'Alice Johnson'
            """.strip(),
            required_objects={
                "tables": {"demo_ecommerce.orders", "demo_ecommerce.customers", "orders", "customers"},
                "columns": {"order_id", "order_date", "total_amount", "customer_id", "customer_name"},
                "joins": {("demo_ecommerce.customers", "")},
            },
        ),

        # 4. implicit_join - Four table join
        EvalSample(
            question_id="q004",
            archetype="implicit_join",
            nl_question="What products did customer Bob Smith order?",
            ground_truth_sql="""
SELECT DISTINCT p.product_name
FROM `demo_ecommerce.customers` c
JOIN `demo_ecommerce.orders` o ON c.customer_id = o.customer_id
JOIN `demo_ecommerce.order_items` oi ON o.order_id = oi.order_id
JOIN `demo_ecommerce.products` p ON oi.product_id = p.product_id
WHERE c.customer_name = 'Bob Smith'
            """.strip(),
            required_objects={
                "tables": {
                    "demo_ecommerce.customers", "demo_ecommerce.orders",
                    "demo_ecommerce.order_items", "demo_ecommerce.products",
                    "customers", "orders", "order_items", "products"
                },
                "columns": {
                    "product_name", "customer_name",
                    "customer_id", "order_id", "product_id"
                },
                "joins": set(),  # Multiple joins
            },
        ),

        # 5. implicit_join - Aggregation with join
        EvalSample(
            question_id="q005",
            archetype="implicit_join",
            nl_question="What is the total revenue by product category?",
            ground_truth_sql="""
SELECT p.category, SUM(oi.quantity * oi.price) as total_revenue
FROM `demo_ecommerce.products` p
JOIN `demo_ecommerce.order_items` oi ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC
            """.strip(),
            required_objects={
                "tables": {"demo_ecommerce.products", "demo_ecommerce.order_items", "products", "order_items"},
                "columns": {"category", "quantity", "price", "product_id"},
                "joins": set(),
            },
        ),

        # 6. ambiguous_column - Multiple price columns (products.price vs order_items.price)
        EvalSample(
            question_id="q006",
            archetype="ambiguous_column",
            nl_question="What is the average price of products in our catalog?",
            ground_truth_sql="""
SELECT AVG(price) as avg_price
FROM `demo_ecommerce.products`
            """.strip(),
            required_objects={
                "tables": {"demo_ecommerce.products", "products"},
                "columns": {"price"},
                "joins": set(),
            },
        ),

        # 8. implicit_join - Complex aggregation
        EvalSample(
            question_id="q007",
            archetype="implicit_join",
            nl_question="How many orders has each customer placed?",
            ground_truth_sql="""
SELECT c.customer_id, c.customer_name, COUNT(o.order_id) as order_count
FROM `demo_ecommerce.customers` c
LEFT JOIN `demo_ecommerce.orders` o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY order_count DESC
            """.strip(),
            required_objects={
                "tables": {"demo_ecommerce.customers", "demo_ecommerce.orders", "customers", "orders"},
                "columns": {"customer_name", "customer_id", "order_id"},
                "joins": set(),
            },
        ),

        # 9. simple_lookup - Temporal query
        EvalSample(
            question_id="q008",
            archetype="simple_lookup",
            nl_question="How many orders were placed in February 2024?",
            ground_truth_sql="""
SELECT COUNT(*) as order_count
FROM `demo_ecommerce.orders`
WHERE order_date >= '2024-02-01' AND order_date < '2024-03-01'
            """.strip(),
            required_objects={
                "tables": {"demo_ecommerce.orders", "orders"},
                "columns": {"order_date"},
                "joins": set(),
            },
        ),

        # 10. implicit_join - Most popular products
        EvalSample(
            question_id="q009",
            archetype="implicit_join",
            nl_question="What are the top 3 most frequently ordered products?",
            ground_truth_sql="""
SELECT p.product_id, p.product_name, COUNT(oi.order_item_id) as times_ordered
FROM `demo_ecommerce.products` p
JOIN `demo_ecommerce.order_items` oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
ORDER BY times_ordered DESC
LIMIT 3
            """.strip(),
            required_objects={
                "tables": {"demo_ecommerce.products", "demo_ecommerce.order_items", "products", "order_items"},
                "columns": {"product_name", "product_id", "order_item_id"},
                "joins": set(),
            },
        ),
    ]


if __name__ == "__main__":
    """Print summary of evaluation samples."""
    samples = get_ecommerce_eval_samples()

    print(f"Total samples: {len(samples)}\n")

    # Count by archetype
    from collections import Counter
    archetypes = Counter(s.archetype for s in samples)

    print("Distribution by archetype:")
    for archetype, count in archetypes.items():
        print(f"  {archetype}: {count}")

    print("\n" + "="*60)
    print("Sample questions:")
    print("="*60)

    for sample in samples:
        print(f"\n[{sample.question_id}] {sample.archetype}")
        print(f"Q: {sample.nl_question}")
        print(f"Tables: {', '.join(sorted(sample.required_objects['tables']))}")
        print(f"Columns: {', '.join(sorted(sample.required_objects['columns']))}")
