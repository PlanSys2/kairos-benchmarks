(define (problem oven-5) (:domain oven) (:objects o1 o2 o3 o4 o5 - oven)
(:init (idle o1) (fresh o1) (= (temp o1) 20) (= (low o1) 40) (= (high o1) 45) (idle o2) (fresh o2) (= (temp o2) 20) (= (low o2) 43) (= (high o2) 48) (idle o3) (fresh o3) (= (temp o3) 20) (= (low o3) 46) (= (high o3) 51) (idle o4) (fresh o4) (= (temp o4) 20) (= (low o4) 49) (= (high o4) 54) (idle o5) (fresh o5) (= (temp o5) 20) (= (low o5) 52) (= (high o5) 57))
(:goal (and (baked o1) (baked o2) (baked o3) (baked o4) (baked o5))))
