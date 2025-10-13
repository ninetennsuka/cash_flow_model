import json

class CashFlowModel:
    """
    DCF — оценка стоимости бизнеса через дисконтирование денежных потоков.
    Ввод: свободный денежный поток, ставка дисконтирования, сроки прогноза.
    """
    def __init__(self, free_cash_flows, discount_rate, terminal_growth):
        self.fcfs = free_cash_flows
        self.discount_rate = discount_rate
        self.terminal_growth = terminal_growth
        self.dcf = {}

    def compute_dcf(self):
        total_pv = 0
        for year, fcf in enumerate(self.fcfs, 1):
            pv = fcf / ((1 + self.discount_rate) ** year)
            total_pv += pv
            self.dcf[f"Year {year}"] = pv
        # Terminal value
        last_fcf = self.fcfs[-1]
        terminal_value = last_fcf * (1 + self.terminal_growth) / (self.discount_rate - self.terminal_growth)
        terminal_pv = terminal_value / ((1 + self.discount_rate) ** len(self.fcfs))
        total_pv += terminal_pv
        self.dcf["Terminal"] = terminal_pv
        return total_pv

    def export_results(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.dcf, f, ensure_ascii=False, indent=3)
        print(f"DCF результаты сохранены в {filename}")

    def print_summary(self):
        total = self.compute_dcf()
        print(f"Итоговая стоимость бизнеса: {total:,.2f} ₽")

if __name__ == "__main__":
    # FCF на 5 лет (млн ₽)
    model = CashFlowModel([10_000_000, 12_000_000, 15_000_000, 20_000_000, 22_000_000], 0.12, 0.03)
    model.print_summary()
    model.export_results("dcf_result.json")
