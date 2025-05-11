import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ApplianceBalancer:
    def __init__(self, bill_calculator):
        """
        Initialize the ApplianceBalancer with a BillCalculator instance.

        Args:
            bill_calculator (BillCalculator): Instance to calculate costs.
        """
        self.bill_calculator = bill_calculator
        logging.debug("ApplianceBalancer initialized")

    def balance_appliances(self, appliances, daily_costs, max_monthly_bill, valid_indices):
        """
        Balance appliance usage to keep the monthly bill below the threshold.
        - Only balance Heater, TV, Ceiling Fan, Air Conditioner, and Microwave.
        - Set maximum usage time for other appliances (excluding Refrigerator, Washing Machine, Smart Plug).

        Args:
            appliances (list): List of appliance dictionaries.
            daily_costs (np.ndarray): Predicted daily costs for each appliance.
            max_monthly_bill (float): Maximum allowed monthly bill.
            valid_indices (list): Indices of appliances that were successfully preprocessed.

        Returns:
            tuple: (adjusted_appliances, adjustments)
                - adjusted_appliances: Updated list of appliances with adjusted usage times.
                - adjustments: Dictionary of adjustments for display.
        """
        # Make a copy of appliances to avoid modifying the original list
        adjusted_appliances = appliances.copy()
        adjustments = {}

        # Calculate the initial total monthly bill
        total_monthly_bill, monthly_costs = self.bill_calculator.calculate_monthly_bill(daily_costs)
        logging.debug(f"Initial monthly bill: ${total_monthly_bill:.2f}, Threshold: ${max_monthly_bill:.2f}")

        # If the total monthly bill is already below the threshold or threshold is invalid, no adjustments needed
        if total_monthly_bill <= max_monthly_bill or max_monthly_bill <= 0:
            logging.debug("No adjustments needed: Bill below threshold or invalid threshold")
            return adjusted_appliances, adjustments

        # Step 1: Separate appliances into categories
        # - Excluded (not adjustable): Refrigerator, Washing Machine, Smart Plug
        # - Balancing list: Heater, TV, Ceiling Fan, Air Conditioner, Microwave
        # - Others: Set maximum usage time (e.g., Smart Bulb, Laptop Charger)
        excluded_indices = []
        balancing_indices = []
        other_indices = []

        for idx, orig_idx in enumerate(valid_indices):
            device_type = adjusted_appliances[orig_idx]["Device Type"]
            if device_type in ["Refrigerator", "Washing Machine", "Smart Plug"]:
                excluded_indices.append((idx, orig_idx))
                logging.debug(f"Skipping {device_type} at index {orig_idx} (excluded from adjustments)")
            elif device_type in ["Heater", "TV", "Ceiling Fan", "Air Conditioner", "Microwave"]:
                balancing_indices.append((idx, orig_idx))
                logging.debug(f"Adding {device_type} at index {orig_idx} to balancing list")
            else:
                other_indices.append((idx, orig_idx))
                logging.debug(f"Adding {device_type} at index {orig_idx} to others list (will set max usage)")

        # Step 2: Allocate budget for non-balancing appliances (others) and set maximum usage
        # Allocate 20% of the threshold to non-balancing appliances (adjustable parameter)
        non_balancing_budget = max_monthly_bill * 0.2
        remaining_budget = max_monthly_bill - non_balancing_budget

        # Calculate total daily cost of excluded appliances
        excluded_daily_cost = sum(daily_costs[idx] for idx, orig_idx in excluded_indices)
        excluded_monthly_cost = excluded_daily_cost * 30
        remaining_budget -= excluded_monthly_cost
        if remaining_budget <= 0:
            logging.warning("Excluded appliances alone exceed the threshold. Cannot balance further.")
            return adjusted_appliances, adjustments

        # Calculate cost per minute for non-balancing appliances (others)
        cost_per_minute_others = {}
        for idx, orig_idx in other_indices:
            appliance = adjusted_appliances[orig_idx]
            usage_minutes = appliance["Usage Duration (minutes)"]
            if usage_minutes > 0:
                cost_per_minute_others[idx] = daily_costs[idx] / usage_minutes
            else:
                cost_per_minute_others[idx] = 0.0

        # Distribute non-balancing budget proportionally and set maximum usage
        total_cost_per_minute_others = sum(
            cost_per_minute_others[idx] for idx in cost_per_minute_others if cost_per_minute_others[idx] > 0
        )
        for idx, orig_idx in other_indices:
            appliance = adjusted_appliances[orig_idx]
            original_usage_minutes = appliance["Usage Duration (minutes)"]
            if original_usage_minutes <= 0:
                continue

            cost_per_minute_val = cost_per_minute_others[idx]
            if cost_per_minute_val <= 0:
                continue

            # Allocate budget proportionally
            allocated_daily_cost = (cost_per_minute_val / total_cost_per_minute_others) * (non_balancing_budget / 30.0)
            max_usage_minutes = allocated_daily_cost / cost_per_minute_val if cost_per_minute_val > 0 else 0
            new_usage_minutes = min(original_usage_minutes, max_usage_minutes)

            if new_usage_minutes < original_usage_minutes:
                adjusted_appliances[orig_idx]["Usage Duration (minutes)"] = new_usage_minutes
                # Calculate reduction percentage
                reduction_percent = ((original_usage_minutes - new_usage_minutes) / original_usage_minutes) * 100
                # Convert to hours for display
                original_usage_hours = original_usage_minutes / 60.0
                new_usage_hours = new_usage_minutes / 60.0
                adjustments[orig_idx] = (
                    f"Set maximum usage to {new_usage_hours:.2f} hours "
                    f"(reduced by {reduction_percent:.1f}% from {original_usage_hours:.2f} hours)"
                )
                # Adjust daily cost
                scale_factor = new_usage_minutes / original_usage_minutes
                daily_costs[idx] *= scale_factor
                logging.debug(f"Set max usage for {appliance['Device Type']}: {new_usage_minutes:.2f} minutes")

        # Step 3: Recalculate remaining bill after setting max usage for others
        total_monthly_bill = np.sum(daily_costs * 30)
        if total_monthly_bill <= max_monthly_bill:
            logging.debug("Bill below threshold after setting max usage for others")
            return adjusted_appliances, adjustments

        # Step 4: Balance the balancing appliances
        if not balancing_indices:
            logging.debug("No appliances in balancing list to adjust")
            return adjusted_appliances, adjustments

        # Calculate cost per minute for balancing appliances
        cost_per_minute = {}
        for idx, orig_idx in balancing_indices:
            appliance = adjusted_appliances[orig_idx]
            usage_minutes = appliance["Usage Duration (minutes)"]
            if usage_minutes > 0:
                cost_per_minute[idx] = daily_costs[idx] / usage_minutes
            else:
                cost_per_minute[idx] = 0.0

        # Adjust usage times iteratively until the bill is below the threshold
        while total_monthly_bill > max_monthly_bill:
            # Calculate the excess cost to reduce
            excess_cost = total_monthly_bill - max_monthly_bill
            logging.debug(f"Excess cost to reduce: ${excess_cost:.2f}")

            # Calculate total cost per minute for balancing appliances
            total_cost_per_minute = sum(
                cost_per_minute[idx]
                for idx, orig_idx in balancing_indices
                if adjusted_appliances[orig_idx]["Usage Duration (minutes)"] > 0
            )

            # If no further adjustments are possible, break the loop
            if total_cost_per_minute <= 0:
                logging.debug("No further usage adjustments possible for balancing appliances")
                break

            # Distribute the reduction proportionally based on cost per minute
            for idx, orig_idx in balancing_indices:
                appliance = adjusted_appliances[orig_idx]
                current_usage_minutes = appliance["Usage Duration (minutes)"]
                original_usage_minutes = appliances[orig_idx]["Usage Duration (minutes)"]

                # Skip if usage is already 0
                if current_usage_minutes <= 0:
                    continue

                cost_per_minute_val = cost_per_minute[idx]
                if cost_per_minute_val <= 0:
                    continue

                # Calculate the proportion of the excess cost to reduce for this appliance
                cost_to_reduce = excess_cost * (cost_per_minute_val / total_cost_per_minute)
                # Convert cost reduction to minutes reduction
                minutes_to_reduce = cost_to_reduce / cost_per_minute_val
                # Calculate new usage minutes, ensuring it doesn't go below 0
                new_usage_minutes = max(current_usage_minutes - minutes_to_reduce, 0)

                if new_usage_minutes < current_usage_minutes:
                    # Update usage duration
                    adjusted_appliances[orig_idx]["Usage Duration (minutes)"] = new_usage_minutes
                    # Calculate reduction percentage
                    reduction_percent = ((current_usage_minutes - new_usage_minutes) / original_usage_minutes) * 100
                    # Convert original and new usage to hours for display
                    original_usage_hours = original_usage_minutes / 60.0
                    new_usage_hours = new_usage_minutes / 60.0
                    # Store adjustment for display
                    adjustments[orig_idx] = (
                        f"Adjusted usage to {new_usage_hours:.2f} hours "
                        f"(reduced by {reduction_percent:.1f}% from {original_usage_hours:.2f} hours)"
                    )

                    # Recalculate daily cost for this appliance with new usage
                    scale_factor = new_usage_minutes / current_usage_minutes if current_usage_minutes > 0 else 0
                    daily_costs[idx] *= scale_factor

            # Recalculate total monthly bill with adjusted costs
            total_monthly_bill = np.sum(daily_costs * 30)

        logging.debug(f"Final adjusted monthly bill: ${total_monthly_bill:.2f}")
        return adjusted_appliances, adjustments