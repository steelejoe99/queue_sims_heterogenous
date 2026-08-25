import unittest

from gi_gi_n_gi_multiclass.core.engine_multi import run_sim_multi
from gi_gi_n_gi_multiclass.core.prehistory import generate_housing_queue_snapshot
from gi_gi_n_gi_multiclass.core.types_multi import (
    CustomerClass,
    InitialQueueCustomer,
    MultiSimConfig,
)
from gi_gi_n_gi_multiclass.dists.common import Deterministic
from gi_gi_n_gi_multiclass.policies.naive_fcfs import NaiveFCFS
from gi_gi_n_gi_multiclass.policies.priority_fcfs import PriorityFCFS


def make_classes():
    return [
        CustomerClass("chronic", Deterministic(0.25), Deterministic(0.0)),
        CustomerClass("transient", Deterministic(0.50), Deterministic(0.0)),
    ]


def make_config(**overrides):
    values = {
        "n_servers": 1,
        "classes": make_classes(),
        "policy": PriorityFCFS(priority_order=[0, 1]),
        "run_time": 1.0,
        "housing_mode": True,
        "first_housing_release": 2.0,
        "housing_release_interval": 2.0,
        "eligibility_delay": 0.0,
    }
    values.update(overrides)
    return MultiSimConfig(**values)


class HousingArrivalModeTests(unittest.TestCase):
    def test_annual_style_batch_arrivals_are_simultaneous(self):
        result = run_sim_multi(
            make_config(
                batch_arrival_counts=[2, 3],
                batch_interval=1.0,
                first_batch_time=0.0,
                last_batch_time=0.0,
            )
        )

        self.assertEqual(len(result.customers), 5)
        self.assertEqual({customer.arrival_time for customer in result.customers}, {0.0})

    def test_monthly_batch_interval_creates_twelve_batches(self):
        result = run_sim_multi(
            make_config(
                batch_arrival_counts=[1, 2],
                batch_interval=1.0 / 12.0,
                first_batch_time=0.0,
                last_batch_time=11.0 / 12.0,
            )
        )

        self.assertEqual(len(result.customers), 36)
        self.assertEqual(
            len({customer.arrival_time for customer in result.customers}),
            12,
        )

    def test_housing_renewal_arrivals_use_class_interarrivals(self):
        result = run_sim_multi(
            make_config(
                housing_arrival_mode="renewal",
                last_arrival_time=1.0,
            )
        )

        self.assertEqual(len(result.customers), 6)
        self.assertEqual(
            sorted(customer.arrival_time for customer in result.customers),
            [0.25, 0.5, 0.5, 0.75, 1.0, 1.0],
        )

    def test_initial_snapshot_preserves_age_and_remaining_eligibility(self):
        result = run_sim_multi(
            make_config(
                n_servers=5,
                initial_queue=[
                    InitialQueueCustomer(0, 0, 0.25, None, 0.25),
                    InitialQueueCustomer(1, 1, 0.75, None, 0.0),
                ],
                first_housing_release=0.5,
                batch_arrival_counts=[0, 0],
                last_batch_time=0.0,
                run_time=0.5,
            )
        )

        self.assertEqual([customer.arrival_time for customer in result.customers], [-0.75, -0.25])
        self.assertEqual([customer.eligibility_time for customer in result.customers], [0.0, 0.25])
        self.assertTrue(all(customer.service_start == 0.5 for customer in result.customers))

    def test_abandoned_customers_are_skipped_in_fcfs_order(self):
        result = run_sim_multi(
            make_config(
                n_servers=1,
                classes=[
                    CustomerClass("chronic", Deterministic(1.0), Deterministic(0.0), Deterministic(0.25)),
                    CustomerClass("transient", Deterministic(1.0), Deterministic(0.0)),
                ],
                initial_queue=[
                    InitialQueueCustomer(0, 0, 1.0, 0.25, 0.0),
                    InitialQueueCustomer(1, 1, 0.5, None, 0.0),
                ],
                first_housing_release=0.5,
                eligibility_delay=0.0,
                batch_arrival_counts=[0, 0],
                last_batch_time=0.0,
                run_time=0.5,
            )
        )

        self.assertEqual(result.customers[0].outcome, "ABANDONED")
        self.assertEqual(result.customers[1].outcome, "SERVED")

    def test_pre_eligibility_abandonment_does_not_schedule_eligibility(self):
        result = run_sim_multi(
            make_config(
                classes=[
                    CustomerClass(
                        "chronic",
                        Deterministic(1.0),
                        Deterministic(0.0),
                        Deterministic(0.25),
                    ),
                    CustomerClass("transient", Deterministic(1.0), Deterministic(0.0)),
                ],
                initial_queue=[InitialQueueCustomer(0, 0, 1.0, 0.25, 0.5)],
                batch_arrival_counts=[0, 0],
                last_batch_time=0.0,
                first_housing_release=1.0,
                eligibility_delay=0.5,
                run_time=0.5,
                collect_event_log=True,
            )
        )

        self.assertEqual(result.customers[0].outcome, "ABANDONED")
        self.assertNotIn("ELIGIBILITY", [event["etype"] for event in result.event_log])

    def test_prehistory_snapshot_reaches_target_and_contains_historical_ages(self):
        snapshot = generate_housing_queue_snapshot(
            make_config(
                housing_arrival_mode="renewal",
                first_housing_release=100.0,
                housing_release_interval=1.0,
                eligibility_delay=0.5,
            ),
            target_population=4,
            max_prehistory_time=2.0,
        )

        self.assertEqual(len(snapshot.customers), 4)
        self.assertTrue(all(customer.age >= 0.0 for customer in snapshot.customers))
        self.assertGreater(snapshot.customers[0].age, snapshot.customers[-1].age)
        self.assertTrue(all(customer.remaining_eligibility >= 0.0 for customer in snapshot.customers))

    def test_naive_fcfs_ignores_class_and_houses_oldest_eligible_customer(self):
        result = run_sim_multi(
            make_config(
                policy=NaiveFCFS(),
                initial_housing_stock=1,
                initial_queue=[
                    InitialQueueCustomer(0, 0, 0.5, None, 0.0),
                    InitialQueueCustomer(1, 1, 1.0, None, 0.0),
                ],
                batch_arrival_counts=[0, 0],
                last_batch_time=0.0,
            )
        )

        served = [customer for customer in result.customers if customer.outcome == "SERVED"]
        self.assertEqual(len(served), 1)
        self.assertEqual(served[0].true_class_id, 1)

    def test_initial_snapshot_can_be_reclassified_at_observation_time(self):
        class AlwaysNonchronic:
            n_classes = 2

            @staticmethod
            def assign(true_class_id, rng):
                return 1

        result = run_sim_multi(
            make_config(
                classifier=AlwaysNonchronic(),
                classify_initial_queue=True,
                initial_queue=[InitialQueueCustomer(0, 0, 1.0, None, 0.0)],
                batch_arrival_counts=[0, 0],
                last_batch_time=0.0,
            )
        )

        self.assertEqual(result.customers[0].true_class_id, 0)
        self.assertEqual(result.customers[0].assigned_class_id, 1)


if __name__ == "__main__":
    unittest.main()
