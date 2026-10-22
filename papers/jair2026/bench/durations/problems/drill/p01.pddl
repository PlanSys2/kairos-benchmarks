(define (problem drill-1) (:domain drill) (:objects h1 - hole)
(:init (bit_free) (= (rate) 1.5) (planned h1) (= (depth h1) 0) (= (min_depth h1) 12) (= (max_depth h1) 15))
(:goal (and (drilled h1))))
