import random
import matplotlib.pyplot as plt
def select_from_dist(item_prob_dist):
    ranreal = random.random()
    for item, prob in item_prob_dist.items():
        if ranreal < prob:
            return item
        ranreal -= prob
    raise RuntimeError(f"{item_prob_dist} is not a valid probability distribution")

class PlotHistory:
    def __init__(self, agent, environment):
        self.agent = agent
        self.environment = environment

    def plot_history(self):
        plt.figure(figsize=(14, 10))

        plt.subplot(2, 1, 1)
        plt.plot(self.environment.price_history, label="Price", color="blue", linewidth=2)
        plt.axhline(
            self.agent.average_price, color="green", linestyle="--", label="Average Price"
        )
        plt.title(
            f"Smartphone Price Trend Over Time\n"
            f"Final Price: {self.environment.price_history[-1]:.2f} BDT | "
            f"Final Average Price: {self.agent.average_price:.2f} BDT"
        )
        plt.ylabel("Price (BDT)")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()

    
        for i, price in enumerate(self.environment.price_history):
            if price < 0.8 * self.agent.average_price:  
                plt.annotate(
                    "Significant Drop",
                    (i, price),
                    textcoords="offset points",
                    xytext=(0, -15),
                    ha="center",
                    fontsize=8,
                    color="red",
                )


        plt.subplot(2, 1, 2)
        plt.plot(
            self.environment.stock_history,
            label="Stock Level",
            color="blue",
            linewidth=2,
        )
        plt.bar(
            range(len(self.agent.buy_history)),
            self.agent.buy_history,
            label="Units Purchased",
            color="orange",
            alpha=0.7,
        )
        plt.title(
            f"Stock Levels and Purchases Over Time\n"
            f"Final Stock: {self.environment.stock_history[-1]} units | "
            f"Total Units Purchased: {sum(self.agent.buy_history)}"
        )
        plt.ylabel("Stock / Purchases")
        plt.xlabel("Time Step")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()

        plt.tight_layout()
        plt.show()



class SmartphoneEnvironment:
    price_delta = [10, -20, 5, -15, 0, 25, -30, 20, -5, 0]
    noise_sd = 5

    def __init__(self):
        self.time = 0
        self.stock = 50
        self.price = 600
        self.stock_history = [self.stock]
        self.price_history = [self.price]

    def initial_percept(self):
        return {"price": self.price, "stock": self.stock}

    def do_action(self, action):
        daily_sales = select_from_dist({3: 0.2, 5: 0.3, 7: 0.3, 10: 0.2})
        bought = action.get("buy", 0)
        self.stock = max(0, self.stock + bought - daily_sales)
        self.time += 1
        self.price += (
            self.price_delta[self.time % len(self.price_delta)]
            + random.gauss(0, self.noise_sd)
        )
        self.stock_history.append(self.stock)
        self.price_history.append(self.price)
        return {"price": self.price, "stock": self.stock}
        
class PriceMonitoringController:
    def __init__(self, agent, discount_threshold=0.2):
        self.agent = agent
        self.discount_threshold = discount_threshold

    def monitor(self, percept):
        current_price = percept["price"]
        if current_price < (1 - self.discount_threshold) * self.agent.average_price:
            return True
        return False


class InventoryMonitoringController:
    def __init__(self, threshold=10):
        self.threshold = threshold

    def monitor(self, percept):
        return percept["stock"] < self.threshold


class OrderingController:
    def __init__(self, price_controller, inventory_controller):
        self.price_controller = price_controller
        self.inventory_controller = inventory_controller

    def order(self, percept):
        current_price = percept["price"]
        
        if self.price_controller.monitor(percept) and not self.inventory_controller.monitor(percept):
            discount_ratio = (self.price_controller.agent.average_price - current_price) / self.price_controller.agent.average_price
            tobuy = int(15 * (1 + discount_ratio))  
            print(f"Discount detected! Discount ratio: {discount_ratio:.2f}. Ordering {tobuy} units.")
            return tobuy
        elif self.inventory_controller.monitor(percept):
            print("Low stock detected. Ordering 10 units.\n\n")
            return 10
        print("No action taken. No significant discount or stock issue.\n\n")
        return 0


# Agent Class
class SmartphoneAgent:
    def __init__(self):
        self.average_price = 600  
        self.buy_history = []
        self.total_spent = 0  

        
        self.price_controller = PriceMonitoringController(self)
        self.inventory_controller = InventoryMonitoringController()
        self.ordering_controller = OrderingController(self.price_controller, self.inventory_controller)

    def select_action(self, percept):
        current_price = percept["price"]
        self.average_price += (current_price - self.average_price) * 0.1

        
        price_discount = self.price_controller.monitor(percept)
        low_stock = self.inventory_controller.monitor(percept)

        
        tobuy = self.ordering_controller.order(percept)
        
        self.total_spent += tobuy * current_price
        self.buy_history.append(tobuy)

        
        print(f"Time: {len(self.buy_history) - 1}")
        print(f"Price: {current_price:.0f}, Stock: {percept['stock']}")
        print(
            f"Price Monitoring: {'Discount detected' if price_discount else 'No discount'} "
            f"(Price: {current_price}, Average: {self.average_price:.0f})"
        )
        print(
            f"Inventory Monitoring: {'Low stock detected' if low_stock else 'Sufficient stock'} "
            f"(Stock: {percept['stock']})"
        )
        print(f"Action: Order {tobuy} units\n")

        return {"buy": tobuy}



class Simulation:
    def __init__(self, agent, environment):
        self.agent = agent
        self.environment = environment
        self.percept = self.environment.initial_percept()

    def run(self, steps):
        for step in range(steps):
            action = self.agent.select_action(self.percept)
            self.percept = self.environment.do_action(action)


if __name__ == "__main__":
    environment = SmartphoneEnvironment()
    agent = SmartphoneAgent()
    simulation = Simulation(agent, environment)
    simulation.run(20)
    plotter = PlotHistory(agent, environment)
    plotter.plot_history()
