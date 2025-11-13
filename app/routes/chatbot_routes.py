from flask import Blueprint, request, jsonify
from app import limiter, db
from openai import OpenAI
from sqlalchemy import func, desc
from app.models.inventory import Inventory
from app.models.employees import Employees
from app.models.vendors import Vendors
from app.models.customers import Customers
from decimal import Decimal
import os
import json

chatbot_bp = Blueprint("chatbot", __name__)

# ============================================================
#                        MEMORY SYSTEM
# ============================================================

agent_memory = {
    "pending_value_calc_items": None,   # last "top items" for follow-up value calc
}

FOLLOWUP_KEYWORDS = [
    "total value",
    "value",
    "worth",
    "calculate",
    "compute",
    "price *",
    "quantity *",
    "price x",
    "quantity x",
    "value of these",
    "value of them",
    "value of those",
    "their value",
    "these value",
    "those value",
    "total value of top",
    "value of top",
    "value of top 2",
    "value of top items",
    "value of the top items",
]


def is_followup_query(q: str) -> bool:
    q = (q or "").lower().strip()
    if not agent_memory["pending_value_calc_items"]:
        return False
    return any(key in q for key in FOLLOWUP_KEYWORDS)


# ============================================================
#                        TOOL DEFINITIONS
# ============================================================

TOOLS = [
    # ===== Inventory Tools =====
    {
        "type": "function",
        "function": {
            "name": "get_inventory_totals",
            "description": "Get total items, quantity, and total value of inventory.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_inventory_items",
            "description": "Get top N items by quantity, price, or total value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["quantity", "price", "value"],
                    },
                    "limit": {"type": "integer"},
                },
                "required": ["metric", "limit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_inventory_items",
            "description": "List ALL inventory items with qty, price, value.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_total_value_for_last_items",
            "description": "Calculate total value of last 'top items' selection.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },

    # ===== Employee Tools =====
    {
        "type": "function",
        "function": {
            "name": "get_employee_count",
            "description": "Return total number of employees.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_employees_basic",
            "description": "Return employee list (name, department, status).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employees_by_department",
            "description": "Return employees from a given department.",
            "parameters": {
                "type": "object",
                "properties": {"department": {"type": "string"}},
                "required": ["department"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_employee_by_name",
            "description": "Search employees by name.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_summary",
            "description": "Return employee overview summary.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },

    # ===== Employee Salary Tools =====
    {
        "type": "function",
        "function": {
            "name": "get_highest_salary",
            "description": "Get the employee with the highest salary.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lowest_salary",
            "description": "Get the employee with the lowest salary.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_n_salaries",
            "description": "Get top N employees by salary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of top employees"},
                },
                "required": ["limit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_salary_summary",
            "description": "Get overall salary summary: highest, lowest, average, median.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_salary_distribution",
            "description": (
                "Get salary distribution stats: min, max, average, median, and quartiles."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_avg_salary_by_department",
            "description": "Get average, min, and max salary for each department.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_highest_salary_per_department",
            "description": "Get highest salary employee per department.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lowest_salary_per_department",
            "description": "Get lowest salary employee per department.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },

    # ===== Vendor Tools =====
    {
        "type": "function",
        "function": {
            "name": "get_vendor_count",
            "description": "Return total number of vendors.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_vendors_basic",
            "description": "Return vendor list (name, contact, phone, category).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_vendor_by_name",
            "description": "Search vendors by name.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_vendor_summary",
            "description": "Vendor overview: total vendors and category breakdown.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },

    # ===== Customer Tools =====
    {
        "type": "function",
        "function": {
            "name": "get_customer_count",
            "description": "Return total number of customers.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_customers_basic",
            "description": "Return customer list (name, phone, address, status).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_customer_by_name",
            "description": "Search customers by name.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_summary",
            "description": "Customer overview: total, active vs inactive.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

# ============================================================
#                     INVENTORY TOOL LOGIC
# ============================================================

def tool_get_inventory_totals():
    total_items = Inventory.query.count()
    total_qty = db.session.query(func.sum(Inventory.quantity)).scalar() or 0
    total_val = (
        db.session.query(func.sum(Inventory.price * Inventory.quantity)).scalar() or 0
    )

    return {
        "total_items": int(total_items),
        "total_quantity": int(total_qty),
        "total_value": float(total_val),
    }


def tool_get_top_inventory_items(metric: str, limit: int):
    limit = int(limit)

    if metric == "quantity":
        rows = Inventory.query.order_by(desc(Inventory.quantity)).limit(limit).all()
        agent_memory["pending_value_calc_items"] = [r.item_name for r in rows]
        return [{"item": r.item_name, "quantity": int(r.quantity)} for r in rows]

    if metric == "price":
        rows = Inventory.query.order_by(desc(Inventory.price)).limit(limit).all()
        agent_memory["pending_value_calc_items"] = [r.item_name for r in rows]
        return [{"item": r.item_name, "price": float(r.price)} for r in rows]

    if metric == "value":
        rows = (
            db.session.query(
                Inventory,
                (Inventory.price * Inventory.quantity).label("value"),
            )
            .order_by(desc("value"))
            .limit(limit)
            .all()
        )
        agent_memory["pending_value_calc_items"] = [inv.item_name for inv, _ in rows]
        return [{"item": inv.item_name, "value": float(value)} for inv, value in rows]

    return {"error": "Invalid metric"}


def tool_get_all_inventory_items():
    rows = Inventory.query.all()
    return [
        {
            "item": r.item_name,
            "quantity": int(r.quantity),
            "price": float(r.price),
            "value": float(r.price * r.quantity),
        }
        for r in rows
    ]


def tool_calculate_total_value_for_last_items():
    items = agent_memory.get("pending_value_calc_items")
    if not items:
        return {"error": "No previous items found for value calculation."}

    breakdown = []
    total = 0

    for name in items:
        rec = Inventory.query.filter_by(item_name=name).first()
        if rec:
            val = rec.price * rec.quantity
            breakdown.append(
                {
                    "item": rec.item_name,
                    "quantity": int(rec.quantity),
                    "price": float(rec.price),
                    "value": float(val),
                }
            )
            total += val

    agent_memory["pending_value_calc_items"] = None

    return {"breakdown": breakdown, "total_value": float(total)}


# ============================================================
#                     EMPLOYEE TOOL LOGIC
# ============================================================

def tool_get_employee_count():
    return {"total_employees": Employees.query.count()}


def tool_get_all_employees_basic():
    rows = Employees.query.order_by(Employees.employee_name).all()
    return [
        {
            "name": e.employee_name,
            "department": e.department,
            "status": e.status,
            "joining_date": e.joining_date.isoformat(),
        }
        for e in rows
    ]


def tool_get_employees_by_department(department: str):
    rows = (
        Employees.query.filter(
            func.lower(Employees.department) == func.lower(department)
        )
        .order_by(Employees.employee_name)
        .all()
    )

    return [
        {
            "name": e.employee_name,
            "department": e.department,
            "status": e.status,
            "joining_date": e.joining_date.isoformat(),
        }
        for e in rows
    ]


def tool_find_employee_by_name(name: str):
    pattern = f"%{name}%"
    rows = Employees.query.filter(
        func.lower(Employees.employee_name).like(func.lower(pattern))
    ).all()

    return [
        {
            "name": e.employee_name,
            "department": e.department,
            "status": e.status,
            "salary": float(e.salary),
            "joining_date": e.joining_date.isoformat(),
        }
        for e in rows
    ]


def tool_get_employee_summary():
    total = Employees.query.count()
    active = Employees.query.filter(func.lower(Employees.status) == "active").count()
    inactive = total - active

    dept_rows = (
        db.session.query(Employees.department, func.count(Employees.id))
        .group_by(Employees.department)
        .all()
    )

    avg_salary = db.session.query(func.avg(Employees.salary)).scalar() or 0
    newest = Employees.query.order_by(desc(Employees.joining_date)).first()
    oldest = Employees.query.order_by(Employees.joining_date).first()

    return {
        "total_employees": int(total),
        "active": int(active),
        "inactive": int(inactive),
        "departments": [{"department": d, "count": int(c)} for d, c in dept_rows],
        "average_salary": float(avg_salary),
        "newest": newest.employee_name if newest else None,
        "oldest": oldest.employee_name if oldest else None,
    }


# ============================================================
#                     SALARY ANALYTICS TOOLS
# ============================================================

def tool_get_highest_salary():
    emp = Employees.query.order_by(desc(Employees.salary)).limit(1).first()
    if not emp:
        return {"error": "No employees found"}
    return {
        "name": emp.employee_name,
        "department": emp.department,
        "salary": float(emp.salary),
    }


def tool_get_lowest_salary():
    emp = Employees.query.order_by(Employees.salary).limit(1).first()
    if not emp:
        return {"error": "No employees found"}
    return {
        "name": emp.employee_name,
        "department": emp.department,
        "salary": float(emp.salary),
    }


def tool_get_top_n_salaries(limit: int):
    limit = int(limit)
    rows = Employees.query.order_by(desc(Employees.salary)).limit(limit).all()
    return [
        {
            "name": e.employee_name,
            "department": e.department,
            "salary": float(e.salary),
        }
        for e in rows
    ]


def tool_get_salary_summary():
    salaries = [e.salary for e in Employees.query.all()]
    if not salaries:
        return {"error": "No employees found"}

    salaries_sorted = sorted(salaries)
    n = len(salaries_sorted)
    mid = n // 2
    if n % 2 == 0:
        median = (salaries_sorted[mid - 1] + salaries_sorted[mid]) / 2
    else:
        median = salaries_sorted[mid]

    highest = max(salaries_sorted)
    lowest = min(salaries_sorted)
    avg = sum(salaries_sorted) / len(salaries_sorted)

    highest_emp = Employees.query.order_by(desc(Employees.salary)).first()
    lowest_emp = Employees.query.order_by(Employees.salary).first()

    return {
        "highest": {
            "name": highest_emp.employee_name,
            "department": highest_emp.department,
            "salary": float(highest),
        },
        "lowest": {
            "name": lowest_emp.employee_name,
            "department": lowest_emp.department,
            "salary": float(lowest),
        },
        "average": float(avg),
        "median": float(median),
    }


def tool_get_salary_distribution():
    rows = Employees.query.all()
    if not rows:
        return {"error": "No employees found"}

    salaries = sorted([e.salary for e in rows])

    def percentile(p):
        k = (len(salaries) - 1) * p
        f = int(k)
        c = min(f + 1, len(salaries) - 1)
        return salaries[f] + (salaries[c] - salaries[f]) * (k - f)

    return {
        "min": float(min(salaries)),
        "max": float(max(salaries)),
        "median": float(percentile(0.5)),
        "p25": float(percentile(0.25)),
        "p75": float(percentile(0.75)),
        "average": float(sum(salaries) / len(salaries)),
    }


def tool_get_avg_salary_by_department():
    rows = (
        db.session.query(
            Employees.department,
            func.avg(Employees.salary),
            func.min(Employees.salary),
            func.max(Employees.salary),
        )
        .group_by(Employees.department)
        .all()
    )

    return [
        {
            "department": d,
            "average": float(avg),
            "min": float(min_s),
            "max": float(max_s),
        }
        for d, avg, min_s, max_s in rows
    ]


def tool_get_highest_salary_per_department():
    depts = db.session.query(Employees.department).distinct().all()
    result = []

    for (dept,) in depts:
        emp = (
            Employees.query.filter_by(department=dept)
            .order_by(desc(Employees.salary))
            .first()
        )
        if emp:
            result.append(
                {
                    "department": dept,
                    "name": emp.employee_name,
                    "salary": float(emp.salary),
                }
            )

    return result


def tool_get_lowest_salary_per_department():
    depts = db.session.query(Employees.department).distinct().all()
    result = []

    for (dept,) in depts:
        emp = (
            Employees.query.filter_by(department=dept)
            .order_by(Employees.salary)
            .first()
        )
        if emp:
            result.append(
                {
                    "department": dept,
                    "name": emp.employee_name,
                    "salary": float(emp.salary),
                }
            )

    return result


# ============================================================
#                     VENDOR TOOL LOGIC
# ============================================================

def tool_get_vendor_count():
    return {"total_vendors": Vendors.query.count()}


def tool_get_all_vendors_basic():
    rows = Vendors.query.order_by(Vendors.vendor_name).all()
    return [
        {
            "name": v.vendor_name,
            "contact_person": v.contact_person,
            "phone": v.phone,
            "category": v.category,
        }
        for v in rows
    ]


def tool_find_vendor_by_name(name: str):
    pattern = f"%{name}%"
    rows = Vendors.query.filter(
        func.lower(Vendors.vendor_name).like(func.lower(pattern))
    ).all()

    return [
        {
            "name": v.vendor_name,
            "contact_person": v.contact_person,
            "phone": v.phone,
            "category": v.category,
        }
        for v in rows
    ]


def tool_get_vendor_summary():
    total = Vendors.query.count()

    category_rows = (
        db.session.query(Vendors.category, func.count(Vendors.id))
        .group_by(Vendors.category)
        .all()
    )

    return {
        "total_vendors": int(total),
        "categories": [{"category": c, "count": int(n)} for c, n in category_rows],
    }


# ============================================================
#                     CUSTOMER TOOL LOGIC
# ============================================================

def tool_get_customer_count():
    return {"total_customers": Customers.query.count()}


def tool_get_all_customers_basic():
    rows = Customers.query.order_by(Customers.customer_name).all()
    return [
        {
            "name": c.customer_name,
            "phone": c.phone,
            "address": c.address,
            "status": c.status,
        }
        for c in rows
    ]


def tool_find_customer_by_name(name: str):
    pattern = f"%{name}%"
    rows = Customers.query.filter(
        func.lower(Customers.customer_name).like(func.lower(pattern))
    ).all()

    return [
        {
            "name": c.customer_name,
            "phone": c.phone,
            "address": c.address,
            "status": c.status,
        }
        for c in rows
    ]


def tool_get_customer_summary():
    total = Customers.query.count()
    active = Customers.query.filter(func.lower(Customers.status) == "active").count()
    inactive = total - active

    return {
        "total_customers": int(total),
        "active": int(active),
        "inactive": int(inactive),
    }


# ============================================================
#                 TOOL DISPATCHER (EXECUTES TOOLS)
# ============================================================

def execute_tool(name, args):
    # Inventory
    if name == "get_inventory_totals":
        return tool_get_inventory_totals()
    if name == "get_top_inventory_items":
        return tool_get_top_inventory_items(args.get("metric"), args.get("limit"))
    if name == "get_all_inventory_items":
        return tool_get_all_inventory_items()
    if name == "calculate_total_value_for_last_items":
        return tool_calculate_total_value_for_last_items()

    # Employees & Salary
    if name == "get_employee_count":
        return tool_get_employee_count()
    if name == "get_all_employees_basic":
        return tool_get_all_employees_basic()
    if name == "get_employees_by_department":
        return tool_get_employees_by_department(args.get("department"))
    if name == "find_employee_by_name":
        return tool_find_employee_by_name(args.get("name"))
    if name == "get_employee_summary":
        return tool_get_employee_summary()
    if name == "get_highest_salary":
        return tool_get_highest_salary()
    if name == "get_lowest_salary":
        return tool_get_lowest_salary()
    if name == "get_top_n_salaries":
        return tool_get_top_n_salaries(args.get("limit"))
    if name == "get_salary_summary":
        return tool_get_salary_summary()
    if name == "get_salary_distribution":
        return tool_get_salary_distribution()
    if name == "get_avg_salary_by_department":
        return tool_get_avg_salary_by_department()
    if name == "get_highest_salary_per_department":
        return tool_get_highest_salary_per_department()
    if name == "get_lowest_salary_per_department":
        return tool_get_lowest_salary_per_department()

    # Vendors
    if name == "get_vendor_count":
        return tool_get_vendor_count()
    if name == "get_all_vendors_basic":
        return tool_get_all_vendors_basic()
    if name == "find_vendor_by_name":
        return tool_find_vendor_by_name(args.get("name"))
    if name == "get_vendor_summary":
        return tool_get_vendor_summary()

    # Customers
    if name == "get_customer_count":
        return tool_get_customer_count()
    if name == "get_all_customers_basic":
        return tool_get_all_customers_basic()
    if name == "find_customer_by_name":
        return tool_find_customer_by_name(args.get("name"))
    if name == "get_customer_summary":
        return tool_get_customer_summary()

    return {"error": f"Unknown tool '{name}'"}


# ============================================================
#                        GPT AGENT CALL
# ============================================================

def call_gpt_agent(client: OpenAI, user_query: str):
    messages = [
        {
            "role": "system",
            "content": (
                "You are an ERP assistant with access to structured database tools. "
                "Use tools to answer questions about inventory, employees, salaries, "
                "vendors, and customers. Never guess data."
            ),
        },
        {"role": "user", "content": user_query},
    ]

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    return response


# ============================================================
#             SAFE JSON (DECIMAL → FLOAT CONVERSION)
# ============================================================

def safe_json(data):
    """Convert Decimals and other non-serializable objects to safe JSON."""
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, dict):
        return {k: safe_json(v) for k, v in data.items()}
    if isinstance(data, list):
        return [safe_json(i) for i in data]
    return data


# ============================================================
#           HANDLE TOOL CALLS (OFFICIAL OPENAI FORMAT)
# ============================================================

def handle_gpt_response(client: OpenAI, response):
    msg = response.choices[0].message

    # If no tool call → return direct text
    if not getattr(msg, "tool_calls", None):
        return msg.content

    final_reply = ""

    for tool_call in msg.tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments or "{}")

        # Execute local Python tool
        result = execute_tool(name, args)
        result = safe_json(result)

        # Build the correct tool message chain
        follow_messages = [
            {
                "role": "system",
                "content": "Format the result cleanly and clearly for the user."
            },
            msg,  # original assistant message with tool_calls
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            }
        ]

        follow = client.chat.completions.create(
            model="gpt-4.1",
            messages=follow_messages
        )

        final_reply = follow.choices[0].message.content

    return final_reply


# ============================================================
#                        MAIN API ROUTE
# ============================================================

@chatbot_bp.route("/api/chatbot", methods=["POST"])
@limiter.limit("10 per minute")
def chatbot():
    data = request.get_json() or {}
    user_query = (data.get("query") or "").strip()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Follow-up like: "total value", "their value", etc.
    if is_followup_query(user_query):
        result = tool_calculate_total_value_for_last_items()
        result = safe_json(result)

        if "breakdown" in result:
            lines = []
            for item in result["breakdown"]:
                lines.append(
                    f"- {item['item']}: {item['quantity']} × ₹{item['price']:,.2f} = ₹{item['value']:,.2f}"
                )
            lines.append(f"\nTotal value = ₹{result['total_value']:,.2f}")
            reply = "\n".join(lines)
        else:
            reply = json.dumps(result, indent=2)
        return jsonify({"reply": reply})

    # Main tool-calling path
    response = call_gpt_agent(client, user_query)
    reply = handle_gpt_response(client, response)

    return jsonify({"reply": reply})
