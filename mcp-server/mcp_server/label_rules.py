"""
Label rules for defects based on order lifecycle and APIs where the order is stuck.
Maps defect title/description and Functional Area to platform labels: Platform-PendingOrderSubmit,
Platform-PendingOrderConfirmation, Platform-Payment, Platform-Shipment, Platform-PendingActivation,
Platform-Promo, Platform-PortIn, Platform-Activation.

Functional Area is used first when available; title/description keywords are used as fallback.
Reference: https://docs.google.com/spreadsheets/d/162JXMTa3fbhZC7gUq1MXvu6q4-dS3T85mHE1IYWA0zc/
"""
import re
from typing import Optional, List, Tuple

# Functional Area value -> Platform label (case-insensitive match)
# Checked before title/description keywords when functional areas are available
FUNCTIONAL_AREA_TO_LABEL: dict = {
    "payment": "Platform-Payment",
    "charge payment": "Platform-Payment",
    "submit payment": "Platform-Payment",
    "order submission": "Platform-PendingOrderSubmit",
    "order submit": "Platform-PendingOrderSubmit",
    "ordersubmission": "Platform-PendingOrderSubmit",
    "order confirmation": "Platform-PendingOrderConfirmation",
    "orderconfirmation": "Platform-PendingOrderConfirmation",
    "shipment": "Platform-Shipment",
    "activation": "Platform-Activation",
    "esim": "Platform-Activation",
    "port": "Platform-PortIn",
    "port in": "Platform-PortIn",
    "promo": "Platform-Promo",
    "promon": "Platform-Promo",
}

# Order of match matters: more specific first
# Payment first; promo+ordersubmit/orderconfirmation before generic promo/port/activation
LABEL_RULES: List[Tuple[str, List[str]]] = [
    # Platform-Payment: payment-specific failures
    (
        "Platform-Payment",
        [
            "void auth payment",
            "void auth",
            "payment failed",
            "payment failure",
            "chargepayment2",
            "charge payment 2",
            "charge-payment-2",
            "cp2",
            "submitpayment",
            "submit payment",
            "submit-payment-2",
            "sp2",
        ],
    ),
    # Promo + OrderSubmit -> Platform-PendingOrderSubmit
    (
        "Platform-PendingOrderSubmit",
        [
            "promo order submit",
            "promo ordersubmission",
            "promo ordersubmit",
            "promon order submit",
            "promon ordersubmission",
        ],
    ),
    # Promo + OrderConfirmation -> Platform-PendingOrderConfirmation
    (
        "Platform-PendingOrderConfirmation",
        [
            "promo order confirmation",
            "promo orderconfirmation",
            "promon order confirmation",
            "promon orderconfirmation",
        ],
    ),
    # Platform-Shipment
    (
        "Platform-Shipment",
        [
            "rdb",
            "dc update sap callback",
            "3pl sap callback",
            "shipment confirmation sap callback",
            "shipment confirmation sap callback (inbound)",
            "shipment callback",
        ],
    ),
    # Platform-Activation: activation, esim, activation+port
    (
        "Platform-Activation",
        [
            "activation",
            "esim",
            "port activation",
            "activation port",
        ],
    ),
    # Platform-PortIn: port-related (not activation)
    (
        "Platform-PortIn",
        [
            "port in",
            "portin",
            "port-in",
            "port transfer",
        ],
    ),
    # Platform-Promo: PROMON/promo related
    (
        "Platform-Promo",
        [
            "promon",
            "promo",
        ],
    ),
    # Platform-PendingActivation
    (
        "Platform-PendingActivation",
        [
            "get-activation-order-info",
            "get activation order info",
            "personalizationprovisioning",
            "personalization provisioning",
            "confirmpersonalization",
            "confirm personalization",
            "parkorder",
            "park order",
            "createorder",
            "create order",
            "update vot",
            "wfm orderconfirmation",
            "wfm order confirmation",
            "shipment confirmation email",
            "activate",
            "orbpm inbound",
            "updateorderlineactivationstatus",
            "update order line activation status",
            "out for delivery",
            "delivered (inbound)",
            "delivered message",
        ],
    ),
    # Platform-PendingOrderConfirmation
    (
        "Platform-PendingOrderConfirmation",
        [
            "order confirmation",
            "orderconfirmation",
            "enforce callback",
            "enforceacknowledgement",
            "enforce acknowledgement",
            "cib callback",
            "save offer",
            "commit offer",
            "createloan",
            "create loan",
            "insertvot",
            "insert vot",
        ],
    ),
    # Platform-PendingOrderSubmit (OrderSubmission level)
    (
        "Platform-PendingOrderSubmit",
        [
            "order submission",
            "ordersubmission",
            "order submit",
            "carttoorderacceptance",
            "cart to order acceptance",
            "inventory check",
            "authorize payment",
            "assignmtn",
            "assign mtn",
            "biocatch",
            "bio catch",
            "preorderwrite",
            "pre order write",
            "generateinstallments",
            "generate installments",
            "modify credit",
            "ctoc",
            "saveloan",
            "save loan",
            "create inventory block",
            "submitpayment",
            "submit payment",
            "derive-tnc",
            "derive tnc",
            "inserttnc",
            "insert tnc",
            "submitfraudcheck",
            "submit fraud check",
            "wfm (ordersubmit)",
            "wfm order submit",
            "create child order",
            "chargepayment2",
            "charge payment 2",
            "update cart status",
        ],
    ),
]


def suggest_label(
    title: str,
    description: str,
    functional_areas: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Suggest a platform label based on Functional Area (first), then title/description.
    functional_areas: list of values from Jira Functional Areas field.
    Returns the first matching label, or None if no match.
    """
    # 1. Check Functional Area first when available
    if functional_areas:
        for fa in functional_areas:
            fa_clean = (fa or "").strip().lower()
            if not fa_clean:
                continue
            for key, label in FUNCTIONAL_AREA_TO_LABEL.items():
                if key in fa_clean:
                    return label

    # 2. Fall back to title/description keywords
    text = f"{title or ''} {description or ''}".lower()
    # Normalize: collapse spaces, treat hyphens as word separators, remove extra punctuation
    text_norm = re.sub(r"[^\w\s-]", " ", text)
    text_norm = re.sub(r"-+", " ", text_norm)  # "charge-payment-2" -> "charge payment 2"
    text_norm = re.sub(r"\s+", " ", text_norm).strip()

    for label, keywords in LABEL_RULES:
        for kw in keywords:
            kw_norm = re.sub(r"[^\w\s-]", " ", kw).lower()
            kw_norm = re.sub(r"\s+", " ", kw_norm).strip()
            if kw_norm in text_norm or kw in text:
                return label
    return None


def suggest_labels_all(title: str, description: str) -> List[str]:
    """
    Return all matching labels (for cases where defect spans multiple areas).
    Usually we want one; use suggest_label for single best match.
    """
    text = f"{title or ''} {description or ''}".lower()
    text_norm = re.sub(r"[^\w\s-]", " ", text)
    text_norm = re.sub(r"-+", " ", text_norm)  # "charge-payment-2" -> "charge payment 2"
    text_norm = re.sub(r"\s+", " ", text_norm).strip()

    found: List[str] = []
    seen_labels: set = set()
    for label, keywords in LABEL_RULES:
        if label in seen_labels:
            continue
        for kw in keywords:
            kw_norm = re.sub(r"[^\w\s-]", " ", kw).lower()
            kw_norm = re.sub(r"\s+", " ", kw_norm).strip()
            if (kw_norm in text_norm or kw in text) and label not in seen_labels:
                found.append(label)
                seen_labels.add(label)
                break
    return found
