import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class BillCalculator:
    def __init__(self, model):
        """
        Initialize the BillCalculator with a trained model.

        Args:
            model: The trained machine learning model for prediction.
        """
        self.model = model
        logging.debug("BillCalculator initialized")

    def calculate_daily_costs(self, scaled_features):
        """
        Calculate the daily energy costs for a list of appliances.

        Args:
            scaled_features (np.ndarray): Scaled features of appliances.

        Returns:
            np.ndarray: Predicted daily costs for each appliance.
        """
        try:
            # Use the model to predict daily costs
            daily_costs = self.model.predict(scaled_features)
            logging.debug(f"Predicted daily costs: {daily_costs}")
            return daily_costs
        except Exception as e:
            logging.error(f"Error predicting daily costs: {str(e)}")
            raise

    def calculate_monthly_bill(self, daily_costs):
        """
        Calculate the monthly bill by scaling daily costs to 30 days.

        Args:
            daily_costs (np.ndarray): Daily costs for each appliance.

        Returns:
            tuple: (total_monthly_bill, monthly_costs)
                - total_monthly_bill (float): Total monthly bill.
                - monthly_costs (np.ndarray): Monthly costs for each appliance.
        """
        # Multiply daily costs by 30 to get monthly costs
        monthly_costs = (daily_costs * 30) / 10
        # Sum to get the total monthly bill
        total_monthly_bill = np.sum(monthly_costs)
        logging.debug(f"Calculated monthly bill: ${total_monthly_bill:.2f}")
        return total_monthly_bill, monthly_costs

    def adjust_usage_for_threshold(self, appliances, daily_costs, max_monthly_bill, valid_indices):
        """
        Adjust usage times to meet the maximum monthly bill threshold by calculating
        the maximum allowed usage time for each appliance.

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
        total_monthly_bill, monthly_costs = self.calculate_monthly_bill(daily_costs)
        logging.debug(f"Initial monthly bill: ${total_monthly_bill:.2f}, Threshold: ${max_monthly_bill:.2f}")

        # If the total monthly bill is already below the threshold or threshold is invalid, no adjustments needed
        if total_monthly_bill <= max_monthly_bill or max_monthly_bill <= 0:
            logging.debug("No adjustments needed: Bill below threshold or invalid threshold")
            return adjusted_appliances, adjustments

        # Step 1: Calculate the target daily cost per appliance to meet the threshold
        # Total target daily cost = max_monthly_bill / 30 days
        target_daily_cost = max_monthly_bill / 30.0
        # Calculate current total daily cost
        current_daily_cost = np.sum(daily_costs)
        # Calculate the reduction factor to scale down costs proportionally
        reduction_factor = target_daily_cost / current_daily_cost if current_daily_cost > 0 else 1.0
        logging.debug(f"Reduction factor to meet threshold: {reduction_factor:.4f}")

        # Step 2: Calculate cost per minute for each appliance
        cost_per_minute = {}
        for idx, (daily_cost, orig_idx) in enumerate(zip(daily_costs, valid_indices)):
            appliance = adjusted_appliances[orig_idx]
            usage_minutes = appliance["Usage Duration (minutes)"]
            if usage_minutes > 0:
                # Cost per minute = daily cost / usage minutes
                cost_per_minute[idx] = daily_cost / usage_minutes
            else:
                cost_per_minute[idx] = 0.0

        # Step 3: Calculate maximum allowed usage time for each appliance
        for idx, (daily_cost, orig_idx) in enumerate(zip(daily_costs, valid_indices)):
            if cost_per_minute[idx] <= 0:
                continue

            appliance = adjusted_appliances[orig_idx]
            original_usage_minutes = appliance["Usage Duration (minutes)"]
            # Target daily cost for this appliance = current daily cost * reduction factor
            target_daily_cost_for_appliance = daily_cost * reduction_factor
            # Maximum allowed usage time = target daily cost / cost per minute
            max_allowed_usage_minutes = target_daily_cost_for_appliance / cost_per_minute[idx]
            # Ensure maximum usage time is at least 50% of original to avoid excessive reduction
            min_allowed_usage_minutes = original_usage_minutes * 0.5
            new_usage_minutes = max(max_allowed_usage_minutes, min_allowed_usage_minutes)

            if new_usage_minutes < original_usage_minutes:
                # Update the appliance's usage duration
                adjusted_appliances[orig_idx]["Usage Duration (minutes)"] = new_usage_minutes
                # Calculate reduction percentage
                reduction_percent = ((original_usage_minutes - new_usage_minutes) / original_usage_minutes) * 100
                # Convert original and new usage to hours for display
                original_usage_hours = original_usage_minutes / 60.0
                new_usage_hours = new_usage_minutes / 60.0
                # Store adjustment for display
                adjustments[orig_idx] = (
                    f"Maximum allowed usage time: {new_usage_hours:.2f} hours "
                    f"(reduced by {reduction_percent:.1f}% from {original_usage_hours:.2f} hours)"
                )

                # Adjust the daily cost proportionally (simplified linear scaling)
                scale_factor = new_usage_minutes / original_usage_minutes
                daily_costs[idx] *= scale_factor
                logging.debug(f"Adjusted appliance {orig_idx}: New usage {new_usage_minutes:.2f} minutes, "
                              f"New daily cost ${daily_costs[idx]:.2f}")

        # Step 4: Verify the new total monthly bill (for logging purposes)
        total_monthly_bill, _ = self.calculate_monthly_bill(daily_costs)
        logging.debug(f"Final adjusted monthly bill: ${total_monthly_bill:.2f}")

        return adjusted_appliances, adjustments