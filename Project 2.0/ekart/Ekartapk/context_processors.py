def cart_summary(request):
    items = request.session.get('cart_items', {})
    if not items:
        items = {str(pid): 1 for pid in request.session.get('cart_ids', [])}
    try:
        count = sum(max(1, int(qty)) for qty in items.values())
    except (TypeError, ValueError, AttributeError):
        count = 0
    return {'global_cart_count': count}
