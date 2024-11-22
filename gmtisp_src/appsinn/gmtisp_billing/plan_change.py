# coding=utf-8
from decimal import Decimal
from django.conf import settings
from .importer import import_name


class PlanChangePolicy(object):
    def _calculate_day_cost(self, plan, uptime_limit):
        """
        Finds most fitted plan pricing for a given uptime_limit, and calculates the day cost.
        """
        if plan.is_free():
            # If plan is free, then cost is always 0
            return Decimal("0.00")

        # Ensure uptime_limit is a positive integer
        if not isinstance(uptime_limit, int) or uptime_limit <= 0:
            raise ValueError("uptime_limit must be a positive integer.")

        plan_quotas = plan.planquota_set.order_by("-quota__uptime_limit").select_related("quota")
        selected_quota = None
        for plan_quota in plan_quotas:
            if plan_quotas.quota.uptime_limit <= uptime_limit:
                selected_quota = plan_quota
                break

        if selected_quota:
            # Calculate day cost with Decimal precision
            return (selected_quota.plan.price / selected_quota.quota.uptime_limit).quantize(Decimal("1.00"))
        
        raise ValueError(f"Plan {plan} has no valid pricings for the given uptime_limit.")

    def _calculate_final_price(self, uptime_limit, day_cost_diff):
        """
        Calculates the final price based on the uptime_limit and day cost difference.
        """
        if day_cost_diff is None:
            return None
        if not isinstance(uptime_limit, int) or uptime_limit < 0:
            raise ValueError("uptime_limit must be a non-negative integer.")
        if not isinstance(day_cost_diff, (Decimal, int)):
            raise TypeError("Day cost difference must be a Decimal or integer.")
        
        # Ensure day_cost_diff is converted to Decimal if it is an integer
        if isinstance(day_cost_diff, int):
            day_cost_diff = Decimal(day_cost_diff)

        return uptime_limit * day_cost_diff

    def get_change_price(self, plan_old, plan_new, uptime_limit):
        """
        Calculates the total price of a plan change. Returns None if no payment is required.
        """
        # Ensure uptime_limit is valid
        if not isinstance(uptime_limit, int) or uptime_limit < 1:
            raise ValueError("uptime_limit must be a positive integer.")

        plan_old_day_cost = self._calculate_day_cost(plan_old, uptime_limit)
        plan_new_day_cost = self._calculate_day_cost(plan_new, uptime_limit)

        if not isinstance(plan_old_day_cost, Decimal) or not isinstance(plan_new_day_cost, Decimal):
            raise TypeError("Day costs must be of type Decimal.")

        # Calculate and return the final price
        if plan_new_day_cost <= plan_old_day_cost:
            return self._calculate_final_price(uptime_limit, None)
        else:
            return self._calculate_final_price(
                uptime_limit, plan_new_day_cost - plan_old_day_cost
            )


class StandardPlanChangePolicy(PlanChangePolicy):
    """
    This plan switch policy follows the rules:
        * user can downgrade a plan for free if the plan is
          cheaper or have exact the same price (additional constant charge can be applied)
        * user need to pay extra amount depending of plans price difference (additional constant charge can be applied)

    Change percent rate while upgrading is defined in ``StandardPlanChangePolicy.UPGRADE_PERCENT_RATE``

    Additional constant charges are:
        * ``StandardPlanChangePolicy.UPGRADE_CHARGE``
        * ``StandardPlanChangePolicy.FREE_UPGRADE``
        * ``StandardPlanChangePolicy.DOWNGRADE_CHARGE``

    .. note:: Example

        User has PlanA which costs monthly (30 days) 20 €. His account will expire in 23 days. He wants to change
        to PlanB which costs monthly (30 days) 50€. Calculations::

            PlanA costs per day 20 €/ 30 days = 0.67 €
            PlanB costs per day 50 €/ 30 days = 1.67 €
            Difference per day between PlanA and PlanB is 1.00 €
            Upgrade percent rate is 10%
            Constant upgrade charge is 0 €
            Switch cost is:
                       23 *            1.00 € *                  10% +                     0 € = 25.30 €
                days_left * cost_diff_per_day * upgrade_percent_rate + constant_upgrade_charge
    """

    UPGRADE_PERCENT_RATE = Decimal("10.0")
    UPGRADE_CHARGE = Decimal("0.0")
    DOWNGRADE_CHARGE = None
    FREE_UPGRADE = Decimal("0.0")

    def _calculate_final_price(self, uptime_limit, day_cost_diff):
        if day_cost_diff is None:
            return self.DOWNGRADE_CHARGE
        cost = (
            uptime_limit * day_cost_diff * (self.UPGRADE_PERCENT_RATE / 100 + 1)
            + self.UPGRADE_CHARGE
        ).quantize(Decimal("1.00"))
        if cost is None or cost < self.FREE_UPGRADE:
            return None
        else:
            return cost


def get_policy():
    policy_class = getattr(
        settings,
        "PLANS_CHANGE_POLICY",
        "gmtisp_billing.plan_change.StandardPlanChangePolicy",
    )
    return import_name(policy_class)()


def get_change_price(userplan, plan):
    policy = get_policy()

    if userplan.expire is not None:
        uptime_limit = userplan.days_left()
    else:
        # Use the default uptime_limit of the new plan
        uptime_limit = 30

    return policy.get_change_price(userplan.plan, plan, uptime_limit)
