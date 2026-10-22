(define (problem oven-1) (:domain oven) (:objects o1 - oven)
(:init (idle o1) (fresh o1) (= (temp o1) 20) (= (low o1) 40) (= (high o1) 45))
(:goal (and (baked o1))))
