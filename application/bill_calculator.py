class BillCalculator:
    def __init__(self, model):
        """
        Initialize the BillCalculator with a prediction model.

        Args:
            model: The machine learning model used for cost prediction.
        """
        self.model = model

    def calculate_daily_costs(self, scaled_features):
        """
        Calculate daily costs for appliances based on scaled features.

        Args:
            scaled_features (numpy.ndarray): Scaled features for appliances.

        Returns:
            list: List of daily costs for each appliance (in cents).
        """
        # Existing implementation (assumed correct, not modified)
        predictions = self.model.predict(scaled_features)
        return predictions.tolist()  # Returns costs in cents

    def calculate_monthly_bill(self, daily_costs):
        """
        Calculate the total monthly bill by summing daily costs and multiplying by 30.

        Args:
            daily_costs (list): List of daily costs for each appliance (in cents).

        Returns:
            tuple: (total_monthly_bill, adjustments)
                - total_monthly_bill (float): Total monthly bill in cents.
                - adjustments (list): List of adjustments (empty for compatibility).
        """
        total_daily_cost = sum(daily_costs)  # Sum daily costs in cents
        total_monthly_bill = total_daily_cost  # Multiply by 30 days
        adjustments = []  # No adjustments needed for this calculation
        return total_monthly_bill, adjustments