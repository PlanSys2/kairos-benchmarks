(define (problem oven-2) (:domain oven) (:objects o1 o2 - oven)
(:init (idle o1) (fresh o1) (= (temp o1) 20) (= (low o1) 40) (= (high o1) 45) (idle o2) (fresh o2) (= (temp o2) 20) (= (low o2) 43) (= (high o2) 48))
(:goal (and (baked o1) (baked o2))))
