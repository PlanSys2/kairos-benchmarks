(define (domain delivery-of-time)
  (:requirements :typing :object-fluents :negative-preconditions :durative-actions
                 :numeric-fluents)
  (:types robot location package)
  (:predicates (connected ?a ?b - location) (idle ?r - robot))
  (:functions (loc ?r - robot) - location (pos ?p - package) - location
              (carrying ?r - robot) - package (dist ?a ?b - location))
  (:durative-action move
    :parameters (?r - robot ?from ?to - location)
    :duration (= ?duration (dist ?from ?to))
    :condition (and (at start (= (loc ?r) ?from)) (at start (idle ?r))
                    (over all (connected ?from ?to)))
    :effect (and (at start (not (idle ?r))) (at start (assign (loc ?r) undefined))
                 (at end (assign (loc ?r) ?to)) (at end (idle ?r))))
  (:durative-action pick
    :parameters (?r - robot ?p - package ?l - location)
    :duration (= ?duration 1)
    :condition (and (at start (idle ?r)) (over all (= (loc ?r) ?l)) (at start (= (pos ?p) ?l))
                    (at start (not (= (carrying ?r) ?p))))
    :effect (and (at start (not (idle ?r))) (at start (assign (pos ?p) undefined))
                 (at end (assign (carrying ?r) ?p)) (at end (idle ?r))))
  (:durative-action drop
    :parameters (?r - robot ?p - package ?l - location)
    :duration (= ?duration 1)
    :condition (and (at start (idle ?r)) (over all (= (loc ?r) ?l))
                    (at start (= (carrying ?r) ?p)))
    :effect (and (at start (not (idle ?r))) (at end (assign (carrying ?r) undefined))
                 (at end (assign (pos ?p) ?l)) (at end (idle ?r)))))
