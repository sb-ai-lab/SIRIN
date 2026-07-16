var Ho = { exports: {} }, Nr = {}, Bo = { exports: {} }, Y = {};
/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Za;
function hf() {
  if (Za) return Y;
  Za = 1;
  var u = Symbol.for("react.element"), a = Symbol.for("react.portal"), c = Symbol.for("react.fragment"), x = Symbol.for("react.strict_mode"), w = Symbol.for("react.profiler"), v = Symbol.for("react.provider"), E = Symbol.for("react.context"), R = Symbol.for("react.forward_ref"), T = Symbol.for("react.suspense"), k = Symbol.for("react.memo"), U = Symbol.for("react.lazy"), q = Symbol.iterator;
  function X(h) {
    return h === null || typeof h != "object" ? null : (h = q && h[q] || h["@@iterator"], typeof h == "function" ? h : null);
  }
  var oe = { isMounted: function() {
    return !1;
  }, enqueueForceUpdate: function() {
  }, enqueueReplaceState: function() {
  }, enqueueSetState: function() {
  } }, me = Object.assign, K = {};
  function Z(h, S, J) {
    this.props = h, this.context = S, this.refs = K, this.updater = J || oe;
  }
  Z.prototype.isReactComponent = {}, Z.prototype.setState = function(h, S) {
    if (typeof h != "object" && typeof h != "function" && h != null) throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
    this.updater.enqueueSetState(this, h, S, "setState");
  }, Z.prototype.forceUpdate = function(h) {
    this.updater.enqueueForceUpdate(this, h, "forceUpdate");
  };
  function ee() {
  }
  ee.prototype = Z.prototype;
  function Ce(h, S, J) {
    this.props = h, this.context = S, this.refs = K, this.updater = J || oe;
  }
  var fe = Ce.prototype = new ee();
  fe.constructor = Ce, me(fe, Z.prototype), fe.isPureReactComponent = !0;
  var ve = Array.isArray, Re = Object.prototype.hasOwnProperty, Se = { current: null }, ge = { key: !0, ref: !0, __self: !0, __source: !0 };
  function se(h, S, J) {
    var Q, _ = {}, $ = null, M = null;
    if (S != null) for (Q in S.ref !== void 0 && (M = S.ref), S.key !== void 0 && ($ = "" + S.key), S) Re.call(S, Q) && !ge.hasOwnProperty(Q) && (_[Q] = S[Q]);
    var b = arguments.length - 2;
    if (b === 1) _.children = J;
    else if (1 < b) {
      for (var pe = Array(b), tn = 0; tn < b; tn++) pe[tn] = arguments[tn + 2];
      _.children = pe;
    }
    if (h && h.defaultProps) for (Q in b = h.defaultProps, b) _[Q] === void 0 && (_[Q] = b[Q]);
    return { $$typeof: u, type: h, key: $, ref: M, props: _, _owner: Se.current };
  }
  function G(h, S) {
    return { $$typeof: u, type: h.type, key: S, ref: h.ref, props: h.props, _owner: h._owner };
  }
  function Fe(h) {
    return typeof h == "object" && h !== null && h.$$typeof === u;
  }
  function Ve(h) {
    var S = { "=": "=0", ":": "=2" };
    return "$" + h.replace(/[=:]/g, function(J) {
      return S[J];
    });
  }
  var ze = /\/+/g;
  function ne(h, S) {
    return typeof h == "object" && h !== null && h.key != null ? Ve("" + h.key) : S.toString(36);
  }
  function we(h, S, J, Q, _) {
    var $ = typeof h;
    ($ === "undefined" || $ === "boolean") && (h = null);
    var M = !1;
    if (h === null) M = !0;
    else switch ($) {
      case "string":
      case "number":
        M = !0;
        break;
      case "object":
        switch (h.$$typeof) {
          case u:
          case a:
            M = !0;
        }
    }
    if (M) return M = h, _ = _(M), h = Q === "" ? "." + ne(M, 0) : Q, ve(_) ? (J = "", h != null && (J = h.replace(ze, "$&/") + "/"), we(_, S, J, "", function(tn) {
      return tn;
    })) : _ != null && (Fe(_) && (_ = G(_, J + (!_.key || M && M.key === _.key ? "" : ("" + _.key).replace(ze, "$&/") + "/") + h)), S.push(_)), 1;
    if (M = 0, Q = Q === "" ? "." : Q + ":", ve(h)) for (var b = 0; b < h.length; b++) {
      $ = h[b];
      var pe = Q + ne($, b);
      M += we($, S, J, pe, _);
    }
    else if (pe = X(h), typeof pe == "function") for (h = pe.call(h), b = 0; !($ = h.next()).done; ) $ = $.value, pe = Q + ne($, b++), M += we($, S, J, pe, _);
    else if ($ === "object") throw S = String(h), Error("Objects are not valid as a React child (found: " + (S === "[object Object]" ? "object with keys {" + Object.keys(h).join(", ") + "}" : S) + "). If you meant to render a collection of children, use an array instead.");
    return M;
  }
  function Pe(h, S, J) {
    if (h == null) return h;
    var Q = [], _ = 0;
    return we(h, Q, "", "", function($) {
      return S.call(J, $, _++);
    }), Q;
  }
  function Te(h) {
    if (h._status === -1) {
      var S = h._result;
      S = S(), S.then(function(J) {
        (h._status === 0 || h._status === -1) && (h._status = 1, h._result = J);
      }, function(J) {
        (h._status === 0 || h._status === -1) && (h._status = 2, h._result = J);
      }), h._status === -1 && (h._status = 0, h._result = S);
    }
    if (h._status === 1) return h._result.default;
    throw h._result;
  }
  var ue = { current: null }, O = { transition: null }, z = { ReactCurrentDispatcher: ue, ReactCurrentBatchConfig: O, ReactCurrentOwner: Se };
  function P() {
    throw Error("act(...) is not supported in production builds of React.");
  }
  return Y.Children = { map: Pe, forEach: function(h, S, J) {
    Pe(h, function() {
      S.apply(this, arguments);
    }, J);
  }, count: function(h) {
    var S = 0;
    return Pe(h, function() {
      S++;
    }), S;
  }, toArray: function(h) {
    return Pe(h, function(S) {
      return S;
    }) || [];
  }, only: function(h) {
    if (!Fe(h)) throw Error("React.Children.only expected to receive a single React element child.");
    return h;
  } }, Y.Component = Z, Y.Fragment = c, Y.Profiler = w, Y.PureComponent = Ce, Y.StrictMode = x, Y.Suspense = T, Y.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = z, Y.act = P, Y.cloneElement = function(h, S, J) {
    if (h == null) throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + h + ".");
    var Q = me({}, h.props), _ = h.key, $ = h.ref, M = h._owner;
    if (S != null) {
      if (S.ref !== void 0 && ($ = S.ref, M = Se.current), S.key !== void 0 && (_ = "" + S.key), h.type && h.type.defaultProps) var b = h.type.defaultProps;
      for (pe in S) Re.call(S, pe) && !ge.hasOwnProperty(pe) && (Q[pe] = S[pe] === void 0 && b !== void 0 ? b[pe] : S[pe]);
    }
    var pe = arguments.length - 2;
    if (pe === 1) Q.children = J;
    else if (1 < pe) {
      b = Array(pe);
      for (var tn = 0; tn < pe; tn++) b[tn] = arguments[tn + 2];
      Q.children = b;
    }
    return { $$typeof: u, type: h.type, key: _, ref: $, props: Q, _owner: M };
  }, Y.createContext = function(h) {
    return h = { $$typeof: E, _currentValue: h, _currentValue2: h, _threadCount: 0, Provider: null, Consumer: null, _defaultValue: null, _globalName: null }, h.Provider = { $$typeof: v, _context: h }, h.Consumer = h;
  }, Y.createElement = se, Y.createFactory = function(h) {
    var S = se.bind(null, h);
    return S.type = h, S;
  }, Y.createRef = function() {
    return { current: null };
  }, Y.forwardRef = function(h) {
    return { $$typeof: R, render: h };
  }, Y.isValidElement = Fe, Y.lazy = function(h) {
    return { $$typeof: U, _payload: { _status: -1, _result: h }, _init: Te };
  }, Y.memo = function(h, S) {
    return { $$typeof: k, type: h, compare: S === void 0 ? null : S };
  }, Y.startTransition = function(h) {
    var S = O.transition;
    O.transition = {};
    try {
      h();
    } finally {
      O.transition = S;
    }
  }, Y.unstable_act = P, Y.useCallback = function(h, S) {
    return ue.current.useCallback(h, S);
  }, Y.useContext = function(h) {
    return ue.current.useContext(h);
  }, Y.useDebugValue = function() {
  }, Y.useDeferredValue = function(h) {
    return ue.current.useDeferredValue(h);
  }, Y.useEffect = function(h, S) {
    return ue.current.useEffect(h, S);
  }, Y.useId = function() {
    return ue.current.useId();
  }, Y.useImperativeHandle = function(h, S, J) {
    return ue.current.useImperativeHandle(h, S, J);
  }, Y.useInsertionEffect = function(h, S) {
    return ue.current.useInsertionEffect(h, S);
  }, Y.useLayoutEffect = function(h, S) {
    return ue.current.useLayoutEffect(h, S);
  }, Y.useMemo = function(h, S) {
    return ue.current.useMemo(h, S);
  }, Y.useReducer = function(h, S, J) {
    return ue.current.useReducer(h, S, J);
  }, Y.useRef = function(h) {
    return ue.current.useRef(h);
  }, Y.useState = function(h) {
    return ue.current.useState(h);
  }, Y.useSyncExternalStore = function(h, S, J) {
    return ue.current.useSyncExternalStore(h, S, J);
  }, Y.useTransition = function() {
    return ue.current.useTransition();
  }, Y.version = "18.3.1", Y;
}
var Ja;
function Qo() {
  return Ja || (Ja = 1, Bo.exports = hf()), Bo.exports;
}
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Ka;
function mf() {
  if (Ka) return Nr;
  Ka = 1;
  var u = Qo(), a = Symbol.for("react.element"), c = Symbol.for("react.fragment"), x = Object.prototype.hasOwnProperty, w = u.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, v = { key: !0, ref: !0, __self: !0, __source: !0 };
  function E(R, T, k) {
    var U, q = {}, X = null, oe = null;
    k !== void 0 && (X = "" + k), T.key !== void 0 && (X = "" + T.key), T.ref !== void 0 && (oe = T.ref);
    for (U in T) x.call(T, U) && !v.hasOwnProperty(U) && (q[U] = T[U]);
    if (R && R.defaultProps) for (U in T = R.defaultProps, T) q[U] === void 0 && (q[U] = T[U]);
    return { $$typeof: a, type: R, key: X, ref: oe, props: q, _owner: w.current };
  }
  return Nr.Fragment = c, Nr.jsx = E, Nr.jsxs = E, Nr;
}
var Qa;
function vf() {
  return Qa || (Qa = 1, Ho.exports = mf()), Ho.exports;
}
var o = vf(), le = Qo(), Ul = {}, Xo = { exports: {} }, en = {}, Zo = { exports: {} }, Jo = {};
/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Ga;
function gf() {
  return Ga || (Ga = 1, (function(u) {
    function a(O, z) {
      var P = O.length;
      O.push(z);
      e: for (; 0 < P; ) {
        var h = P - 1 >>> 1, S = O[h];
        if (0 < w(S, z)) O[h] = z, O[P] = S, P = h;
        else break e;
      }
    }
    function c(O) {
      return O.length === 0 ? null : O[0];
    }
    function x(O) {
      if (O.length === 0) return null;
      var z = O[0], P = O.pop();
      if (P !== z) {
        O[0] = P;
        e: for (var h = 0, S = O.length, J = S >>> 1; h < J; ) {
          var Q = 2 * (h + 1) - 1, _ = O[Q], $ = Q + 1, M = O[$];
          if (0 > w(_, P)) $ < S && 0 > w(M, _) ? (O[h] = M, O[$] = P, h = $) : (O[h] = _, O[Q] = P, h = Q);
          else if ($ < S && 0 > w(M, P)) O[h] = M, O[$] = P, h = $;
          else break e;
        }
      }
      return z;
    }
    function w(O, z) {
      var P = O.sortIndex - z.sortIndex;
      return P !== 0 ? P : O.id - z.id;
    }
    if (typeof performance == "object" && typeof performance.now == "function") {
      var v = performance;
      u.unstable_now = function() {
        return v.now();
      };
    } else {
      var E = Date, R = E.now();
      u.unstable_now = function() {
        return E.now() - R;
      };
    }
    var T = [], k = [], U = 1, q = null, X = 3, oe = !1, me = !1, K = !1, Z = typeof setTimeout == "function" ? setTimeout : null, ee = typeof clearTimeout == "function" ? clearTimeout : null, Ce = typeof setImmediate < "u" ? setImmediate : null;
    typeof navigator < "u" && navigator.scheduling !== void 0 && navigator.scheduling.isInputPending !== void 0 && navigator.scheduling.isInputPending.bind(navigator.scheduling);
    function fe(O) {
      for (var z = c(k); z !== null; ) {
        if (z.callback === null) x(k);
        else if (z.startTime <= O) x(k), z.sortIndex = z.expirationTime, a(T, z);
        else break;
        z = c(k);
      }
    }
    function ve(O) {
      if (K = !1, fe(O), !me) if (c(T) !== null) me = !0, Te(Re);
      else {
        var z = c(k);
        z !== null && ue(ve, z.startTime - O);
      }
    }
    function Re(O, z) {
      me = !1, K && (K = !1, ee(se), se = -1), oe = !0;
      var P = X;
      try {
        for (fe(z), q = c(T); q !== null && (!(q.expirationTime > z) || O && !Ve()); ) {
          var h = q.callback;
          if (typeof h == "function") {
            q.callback = null, X = q.priorityLevel;
            var S = h(q.expirationTime <= z);
            z = u.unstable_now(), typeof S == "function" ? q.callback = S : q === c(T) && x(T), fe(z);
          } else x(T);
          q = c(T);
        }
        if (q !== null) var J = !0;
        else {
          var Q = c(k);
          Q !== null && ue(ve, Q.startTime - z), J = !1;
        }
        return J;
      } finally {
        q = null, X = P, oe = !1;
      }
    }
    var Se = !1, ge = null, se = -1, G = 5, Fe = -1;
    function Ve() {
      return !(u.unstable_now() - Fe < G);
    }
    function ze() {
      if (ge !== null) {
        var O = u.unstable_now();
        Fe = O;
        var z = !0;
        try {
          z = ge(!0, O);
        } finally {
          z ? ne() : (Se = !1, ge = null);
        }
      } else Se = !1;
    }
    var ne;
    if (typeof Ce == "function") ne = function() {
      Ce(ze);
    };
    else if (typeof MessageChannel < "u") {
      var we = new MessageChannel(), Pe = we.port2;
      we.port1.onmessage = ze, ne = function() {
        Pe.postMessage(null);
      };
    } else ne = function() {
      Z(ze, 0);
    };
    function Te(O) {
      ge = O, Se || (Se = !0, ne());
    }
    function ue(O, z) {
      se = Z(function() {
        O(u.unstable_now());
      }, z);
    }
    u.unstable_IdlePriority = 5, u.unstable_ImmediatePriority = 1, u.unstable_LowPriority = 4, u.unstable_NormalPriority = 3, u.unstable_Profiling = null, u.unstable_UserBlockingPriority = 2, u.unstable_cancelCallback = function(O) {
      O.callback = null;
    }, u.unstable_continueExecution = function() {
      me || oe || (me = !0, Te(Re));
    }, u.unstable_forceFrameRate = function(O) {
      0 > O || 125 < O ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : G = 0 < O ? Math.floor(1e3 / O) : 5;
    }, u.unstable_getCurrentPriorityLevel = function() {
      return X;
    }, u.unstable_getFirstCallbackNode = function() {
      return c(T);
    }, u.unstable_next = function(O) {
      switch (X) {
        case 1:
        case 2:
        case 3:
          var z = 3;
          break;
        default:
          z = X;
      }
      var P = X;
      X = z;
      try {
        return O();
      } finally {
        X = P;
      }
    }, u.unstable_pauseExecution = function() {
    }, u.unstable_requestPaint = function() {
    }, u.unstable_runWithPriority = function(O, z) {
      switch (O) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
          break;
        default:
          O = 3;
      }
      var P = X;
      X = O;
      try {
        return z();
      } finally {
        X = P;
      }
    }, u.unstable_scheduleCallback = function(O, z, P) {
      var h = u.unstable_now();
      switch (typeof P == "object" && P !== null ? (P = P.delay, P = typeof P == "number" && 0 < P ? h + P : h) : P = h, O) {
        case 1:
          var S = -1;
          break;
        case 2:
          S = 250;
          break;
        case 5:
          S = 1073741823;
          break;
        case 4:
          S = 1e4;
          break;
        default:
          S = 5e3;
      }
      return S = P + S, O = { id: U++, callback: z, priorityLevel: O, startTime: P, expirationTime: S, sortIndex: -1 }, P > h ? (O.sortIndex = P, a(k, O), c(T) === null && O === c(k) && (K ? (ee(se), se = -1) : K = !0, ue(ve, P - h))) : (O.sortIndex = S, a(T, O), me || oe || (me = !0, Te(Re))), O;
    }, u.unstable_shouldYield = Ve, u.unstable_wrapCallback = function(O) {
      var z = X;
      return function() {
        var P = X;
        X = z;
        try {
          return O.apply(this, arguments);
        } finally {
          X = P;
        }
      };
    };
  })(Jo)), Jo;
}
var Ya;
function yf() {
  return Ya || (Ya = 1, Zo.exports = gf()), Zo.exports;
}
/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var ba;
function xf() {
  if (ba) return en;
  ba = 1;
  var u = Qo(), a = yf();
  function c(e) {
    for (var n = "https://reactjs.org/docs/error-decoder.html?invariant=" + e, t = 1; t < arguments.length; t++) n += "&args[]=" + encodeURIComponent(arguments[t]);
    return "Minified React error #" + e + "; visit " + n + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
  }
  var x = /* @__PURE__ */ new Set(), w = {};
  function v(e, n) {
    E(e, n), E(e + "Capture", n);
  }
  function E(e, n) {
    for (w[e] = n, e = 0; e < n.length; e++) x.add(n[e]);
  }
  var R = !(typeof window > "u" || typeof window.document > "u" || typeof window.document.createElement > "u"), T = Object.prototype.hasOwnProperty, k = /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/, U = {}, q = {};
  function X(e) {
    return T.call(q, e) ? !0 : T.call(U, e) ? !1 : k.test(e) ? q[e] = !0 : (U[e] = !0, !1);
  }
  function oe(e, n, t, r) {
    if (t !== null && t.type === 0) return !1;
    switch (typeof n) {
      case "function":
      case "symbol":
        return !0;
      case "boolean":
        return r ? !1 : t !== null ? !t.acceptsBooleans : (e = e.toLowerCase().slice(0, 5), e !== "data-" && e !== "aria-");
      default:
        return !1;
    }
  }
  function me(e, n, t, r) {
    if (n === null || typeof n > "u" || oe(e, n, t, r)) return !0;
    if (r) return !1;
    if (t !== null) switch (t.type) {
      case 3:
        return !n;
      case 4:
        return n === !1;
      case 5:
        return isNaN(n);
      case 6:
        return isNaN(n) || 1 > n;
    }
    return !1;
  }
  function K(e, n, t, r, l, i, s) {
    this.acceptsBooleans = n === 2 || n === 3 || n === 4, this.attributeName = r, this.attributeNamespace = l, this.mustUseProperty = t, this.propertyName = e, this.type = n, this.sanitizeURL = i, this.removeEmptyString = s;
  }
  var Z = {};
  "children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(e) {
    Z[e] = new K(e, 0, !1, e, null, !1, !1);
  }), [["acceptCharset", "accept-charset"], ["className", "class"], ["htmlFor", "for"], ["httpEquiv", "http-equiv"]].forEach(function(e) {
    var n = e[0];
    Z[n] = new K(n, 1, !1, e[1], null, !1, !1);
  }), ["contentEditable", "draggable", "spellCheck", "value"].forEach(function(e) {
    Z[e] = new K(e, 2, !1, e.toLowerCase(), null, !1, !1);
  }), ["autoReverse", "externalResourcesRequired", "focusable", "preserveAlpha"].forEach(function(e) {
    Z[e] = new K(e, 2, !1, e, null, !1, !1);
  }), "allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(e) {
    Z[e] = new K(e, 3, !1, e.toLowerCase(), null, !1, !1);
  }), ["checked", "multiple", "muted", "selected"].forEach(function(e) {
    Z[e] = new K(e, 3, !0, e, null, !1, !1);
  }), ["capture", "download"].forEach(function(e) {
    Z[e] = new K(e, 4, !1, e, null, !1, !1);
  }), ["cols", "rows", "size", "span"].forEach(function(e) {
    Z[e] = new K(e, 6, !1, e, null, !1, !1);
  }), ["rowSpan", "start"].forEach(function(e) {
    Z[e] = new K(e, 5, !1, e.toLowerCase(), null, !1, !1);
  });
  var ee = /[\-:]([a-z])/g;
  function Ce(e) {
    return e[1].toUpperCase();
  }
  "accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(e) {
    var n = e.replace(
      ee,
      Ce
    );
    Z[n] = new K(n, 1, !1, e, null, !1, !1);
  }), "xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(e) {
    var n = e.replace(ee, Ce);
    Z[n] = new K(n, 1, !1, e, "http://www.w3.org/1999/xlink", !1, !1);
  }), ["xml:base", "xml:lang", "xml:space"].forEach(function(e) {
    var n = e.replace(ee, Ce);
    Z[n] = new K(n, 1, !1, e, "http://www.w3.org/XML/1998/namespace", !1, !1);
  }), ["tabIndex", "crossOrigin"].forEach(function(e) {
    Z[e] = new K(e, 1, !1, e.toLowerCase(), null, !1, !1);
  }), Z.xlinkHref = new K("xlinkHref", 1, !1, "xlink:href", "http://www.w3.org/1999/xlink", !0, !1), ["src", "href", "action", "formAction"].forEach(function(e) {
    Z[e] = new K(e, 1, !1, e.toLowerCase(), null, !0, !0);
  });
  function fe(e, n, t, r) {
    var l = Z.hasOwnProperty(n) ? Z[n] : null;
    (l !== null ? l.type !== 0 : r || !(2 < n.length) || n[0] !== "o" && n[0] !== "O" || n[1] !== "n" && n[1] !== "N") && (me(n, t, l, r) && (t = null), r || l === null ? X(n) && (t === null ? e.removeAttribute(n) : e.setAttribute(n, "" + t)) : l.mustUseProperty ? e[l.propertyName] = t === null ? l.type === 3 ? !1 : "" : t : (n = l.attributeName, r = l.attributeNamespace, t === null ? e.removeAttribute(n) : (l = l.type, t = l === 3 || l === 4 && t === !0 ? "" : "" + t, r ? e.setAttributeNS(r, n, t) : e.setAttribute(n, t))));
  }
  var ve = u.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, Re = Symbol.for("react.element"), Se = Symbol.for("react.portal"), ge = Symbol.for("react.fragment"), se = Symbol.for("react.strict_mode"), G = Symbol.for("react.profiler"), Fe = Symbol.for("react.provider"), Ve = Symbol.for("react.context"), ze = Symbol.for("react.forward_ref"), ne = Symbol.for("react.suspense"), we = Symbol.for("react.suspense_list"), Pe = Symbol.for("react.memo"), Te = Symbol.for("react.lazy"), ue = Symbol.for("react.offscreen"), O = Symbol.iterator;
  function z(e) {
    return e === null || typeof e != "object" ? null : (e = O && e[O] || e["@@iterator"], typeof e == "function" ? e : null);
  }
  var P = Object.assign, h;
  function S(e) {
    if (h === void 0) try {
      throw Error();
    } catch (t) {
      var n = t.stack.trim().match(/\n( *(at )?)/);
      h = n && n[1] || "";
    }
    return `
` + h + e;
  }
  var J = !1;
  function Q(e, n) {
    if (!e || J) return "";
    J = !0;
    var t = Error.prepareStackTrace;
    Error.prepareStackTrace = void 0;
    try {
      if (n) if (n = function() {
        throw Error();
      }, Object.defineProperty(n.prototype, "props", { set: function() {
        throw Error();
      } }), typeof Reflect == "object" && Reflect.construct) {
        try {
          Reflect.construct(n, []);
        } catch (y) {
          var r = y;
        }
        Reflect.construct(e, [], n);
      } else {
        try {
          n.call();
        } catch (y) {
          r = y;
        }
        e.call(n.prototype);
      }
      else {
        try {
          throw Error();
        } catch (y) {
          r = y;
        }
        e();
      }
    } catch (y) {
      if (y && r && typeof y.stack == "string") {
        for (var l = y.stack.split(`
`), i = r.stack.split(`
`), s = l.length - 1, d = i.length - 1; 1 <= s && 0 <= d && l[s] !== i[d]; ) d--;
        for (; 1 <= s && 0 <= d; s--, d--) if (l[s] !== i[d]) {
          if (s !== 1 || d !== 1)
            do
              if (s--, d--, 0 > d || l[s] !== i[d]) {
                var f = `
` + l[s].replace(" at new ", " at ");
                return e.displayName && f.includes("<anonymous>") && (f = f.replace("<anonymous>", e.displayName)), f;
              }
            while (1 <= s && 0 <= d);
          break;
        }
      }
    } finally {
      J = !1, Error.prepareStackTrace = t;
    }
    return (e = e ? e.displayName || e.name : "") ? S(e) : "";
  }
  function _(e) {
    switch (e.tag) {
      case 5:
        return S(e.type);
      case 16:
        return S("Lazy");
      case 13:
        return S("Suspense");
      case 19:
        return S("SuspenseList");
      case 0:
      case 2:
      case 15:
        return e = Q(e.type, !1), e;
      case 11:
        return e = Q(e.type.render, !1), e;
      case 1:
        return e = Q(e.type, !0), e;
      default:
        return "";
    }
  }
  function $(e) {
    if (e == null) return null;
    if (typeof e == "function") return e.displayName || e.name || null;
    if (typeof e == "string") return e;
    switch (e) {
      case ge:
        return "Fragment";
      case Se:
        return "Portal";
      case G:
        return "Profiler";
      case se:
        return "StrictMode";
      case ne:
        return "Suspense";
      case we:
        return "SuspenseList";
    }
    if (typeof e == "object") switch (e.$$typeof) {
      case Ve:
        return (e.displayName || "Context") + ".Consumer";
      case Fe:
        return (e._context.displayName || "Context") + ".Provider";
      case ze:
        var n = e.render;
        return e = e.displayName, e || (e = n.displayName || n.name || "", e = e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef"), e;
      case Pe:
        return n = e.displayName || null, n !== null ? n : $(e.type) || "Memo";
      case Te:
        n = e._payload, e = e._init;
        try {
          return $(e(n));
        } catch {
        }
    }
    return null;
  }
  function M(e) {
    var n = e.type;
    switch (e.tag) {
      case 24:
        return "Cache";
      case 9:
        return (n.displayName || "Context") + ".Consumer";
      case 10:
        return (n._context.displayName || "Context") + ".Provider";
      case 18:
        return "DehydratedFragment";
      case 11:
        return e = n.render, e = e.displayName || e.name || "", n.displayName || (e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef");
      case 7:
        return "Fragment";
      case 5:
        return n;
      case 4:
        return "Portal";
      case 3:
        return "Root";
      case 6:
        return "Text";
      case 16:
        return $(n);
      case 8:
        return n === se ? "StrictMode" : "Mode";
      case 22:
        return "Offscreen";
      case 12:
        return "Profiler";
      case 21:
        return "Scope";
      case 13:
        return "Suspense";
      case 19:
        return "SuspenseList";
      case 25:
        return "TracingMarker";
      case 1:
      case 0:
      case 17:
      case 2:
      case 14:
      case 15:
        if (typeof n == "function") return n.displayName || n.name || null;
        if (typeof n == "string") return n;
    }
    return null;
  }
  function b(e) {
    switch (typeof e) {
      case "boolean":
      case "number":
      case "string":
      case "undefined":
        return e;
      case "object":
        return e;
      default:
        return "";
    }
  }
  function pe(e) {
    var n = e.type;
    return (e = e.nodeName) && e.toLowerCase() === "input" && (n === "checkbox" || n === "radio");
  }
  function tn(e) {
    var n = pe(e) ? "checked" : "value", t = Object.getOwnPropertyDescriptor(e.constructor.prototype, n), r = "" + e[n];
    if (!e.hasOwnProperty(n) && typeof t < "u" && typeof t.get == "function" && typeof t.set == "function") {
      var l = t.get, i = t.set;
      return Object.defineProperty(e, n, { configurable: !0, get: function() {
        return l.call(this);
      }, set: function(s) {
        r = "" + s, i.call(this, s);
      } }), Object.defineProperty(e, n, { enumerable: t.enumerable }), { getValue: function() {
        return r;
      }, setValue: function(s) {
        r = "" + s;
      }, stopTracking: function() {
        e._valueTracker = null, delete e[n];
      } };
    }
  }
  function Pr(e) {
    e._valueTracker || (e._valueTracker = tn(e));
  }
  function bo(e) {
    if (!e) return !1;
    var n = e._valueTracker;
    if (!n) return !0;
    var t = n.getValue(), r = "";
    return e && (r = pe(e) ? e.checked ? "true" : "false" : e.value), e = r, e !== t ? (n.setValue(e), !0) : !1;
  }
  function Tr(e) {
    if (e = e || (typeof document < "u" ? document : void 0), typeof e > "u") return null;
    try {
      return e.activeElement || e.body;
    } catch {
      return e.body;
    }
  }
  function Ql(e, n) {
    var t = n.checked;
    return P({}, n, { defaultChecked: void 0, defaultValue: void 0, value: void 0, checked: t ?? e._wrapperState.initialChecked });
  }
  function _o(e, n) {
    var t = n.defaultValue == null ? "" : n.defaultValue, r = n.checked != null ? n.checked : n.defaultChecked;
    t = b(n.value != null ? n.value : t), e._wrapperState = { initialChecked: r, initialValue: t, controlled: n.type === "checkbox" || n.type === "radio" ? n.checked != null : n.value != null };
  }
  function $o(e, n) {
    n = n.checked, n != null && fe(e, "checked", n, !1);
  }
  function Gl(e, n) {
    $o(e, n);
    var t = b(n.value), r = n.type;
    if (t != null) r === "number" ? (t === 0 && e.value === "" || e.value != t) && (e.value = "" + t) : e.value !== "" + t && (e.value = "" + t);
    else if (r === "submit" || r === "reset") {
      e.removeAttribute("value");
      return;
    }
    n.hasOwnProperty("value") ? Yl(e, n.type, t) : n.hasOwnProperty("defaultValue") && Yl(e, n.type, b(n.defaultValue)), n.checked == null && n.defaultChecked != null && (e.defaultChecked = !!n.defaultChecked);
  }
  function es(e, n, t) {
    if (n.hasOwnProperty("value") || n.hasOwnProperty("defaultValue")) {
      var r = n.type;
      if (!(r !== "submit" && r !== "reset" || n.value !== void 0 && n.value !== null)) return;
      n = "" + e._wrapperState.initialValue, t || n === e.value || (e.value = n), e.defaultValue = n;
    }
    t = e.name, t !== "" && (e.name = ""), e.defaultChecked = !!e._wrapperState.initialChecked, t !== "" && (e.name = t);
  }
  function Yl(e, n, t) {
    (n !== "number" || Tr(e.ownerDocument) !== e) && (t == null ? e.defaultValue = "" + e._wrapperState.initialValue : e.defaultValue !== "" + t && (e.defaultValue = "" + t));
  }
  var Ut = Array.isArray;
  function ht(e, n, t, r) {
    if (e = e.options, n) {
      n = {};
      for (var l = 0; l < t.length; l++) n["$" + t[l]] = !0;
      for (t = 0; t < e.length; t++) l = n.hasOwnProperty("$" + e[t].value), e[t].selected !== l && (e[t].selected = l), l && r && (e[t].defaultSelected = !0);
    } else {
      for (t = "" + b(t), n = null, l = 0; l < e.length; l++) {
        if (e[l].value === t) {
          e[l].selected = !0, r && (e[l].defaultSelected = !0);
          return;
        }
        n !== null || e[l].disabled || (n = e[l]);
      }
      n !== null && (n.selected = !0);
    }
  }
  function bl(e, n) {
    if (n.dangerouslySetInnerHTML != null) throw Error(c(91));
    return P({}, n, { value: void 0, defaultValue: void 0, children: "" + e._wrapperState.initialValue });
  }
  function ns(e, n) {
    var t = n.value;
    if (t == null) {
      if (t = n.children, n = n.defaultValue, t != null) {
        if (n != null) throw Error(c(92));
        if (Ut(t)) {
          if (1 < t.length) throw Error(c(93));
          t = t[0];
        }
        n = t;
      }
      n == null && (n = ""), t = n;
    }
    e._wrapperState = { initialValue: b(t) };
  }
  function ts(e, n) {
    var t = b(n.value), r = b(n.defaultValue);
    t != null && (t = "" + t, t !== e.value && (e.value = t), n.defaultValue == null && e.defaultValue !== t && (e.defaultValue = t)), r != null && (e.defaultValue = "" + r);
  }
  function rs(e) {
    var n = e.textContent;
    n === e._wrapperState.initialValue && n !== "" && n !== null && (e.value = n);
  }
  function ls(e) {
    switch (e) {
      case "svg":
        return "http://www.w3.org/2000/svg";
      case "math":
        return "http://www.w3.org/1998/Math/MathML";
      default:
        return "http://www.w3.org/1999/xhtml";
    }
  }
  function _l(e, n) {
    return e == null || e === "http://www.w3.org/1999/xhtml" ? ls(n) : e === "http://www.w3.org/2000/svg" && n === "foreignObject" ? "http://www.w3.org/1999/xhtml" : e;
  }
  var Lr, is = (function(e) {
    return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction ? function(n, t, r, l) {
      MSApp.execUnsafeLocalFunction(function() {
        return e(n, t, r, l);
      });
    } : e;
  })(function(e, n) {
    if (e.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in e) e.innerHTML = n;
    else {
      for (Lr = Lr || document.createElement("div"), Lr.innerHTML = "<svg>" + n.valueOf().toString() + "</svg>", n = Lr.firstChild; e.firstChild; ) e.removeChild(e.firstChild);
      for (; n.firstChild; ) e.appendChild(n.firstChild);
    }
  });
  function qt(e, n) {
    if (n) {
      var t = e.firstChild;
      if (t && t === e.lastChild && t.nodeType === 3) {
        t.nodeValue = n;
        return;
      }
    }
    e.textContent = n;
  }
  var At = {
    animationIterationCount: !0,
    aspectRatio: !0,
    borderImageOutset: !0,
    borderImageSlice: !0,
    borderImageWidth: !0,
    boxFlex: !0,
    boxFlexGroup: !0,
    boxOrdinalGroup: !0,
    columnCount: !0,
    columns: !0,
    flex: !0,
    flexGrow: !0,
    flexPositive: !0,
    flexShrink: !0,
    flexNegative: !0,
    flexOrder: !0,
    gridArea: !0,
    gridRow: !0,
    gridRowEnd: !0,
    gridRowSpan: !0,
    gridRowStart: !0,
    gridColumn: !0,
    gridColumnEnd: !0,
    gridColumnSpan: !0,
    gridColumnStart: !0,
    fontWeight: !0,
    lineClamp: !0,
    lineHeight: !0,
    opacity: !0,
    order: !0,
    orphans: !0,
    tabSize: !0,
    widows: !0,
    zIndex: !0,
    zoom: !0,
    fillOpacity: !0,
    floodOpacity: !0,
    stopOpacity: !0,
    strokeDasharray: !0,
    strokeDashoffset: !0,
    strokeMiterlimit: !0,
    strokeOpacity: !0,
    strokeWidth: !0
  }, gc = ["Webkit", "ms", "Moz", "O"];
  Object.keys(At).forEach(function(e) {
    gc.forEach(function(n) {
      n = n + e.charAt(0).toUpperCase() + e.substring(1), At[n] = At[e];
    });
  });
  function os(e, n, t) {
    return n == null || typeof n == "boolean" || n === "" ? "" : t || typeof n != "number" || n === 0 || At.hasOwnProperty(e) && At[e] ? ("" + n).trim() : n + "px";
  }
  function ss(e, n) {
    e = e.style;
    for (var t in n) if (n.hasOwnProperty(t)) {
      var r = t.indexOf("--") === 0, l = os(t, n[t], r);
      t === "float" && (t = "cssFloat"), r ? e.setProperty(t, l) : e[t] = l;
    }
  }
  var yc = P({ menuitem: !0 }, { area: !0, base: !0, br: !0, col: !0, embed: !0, hr: !0, img: !0, input: !0, keygen: !0, link: !0, meta: !0, param: !0, source: !0, track: !0, wbr: !0 });
  function $l(e, n) {
    if (n) {
      if (yc[e] && (n.children != null || n.dangerouslySetInnerHTML != null)) throw Error(c(137, e));
      if (n.dangerouslySetInnerHTML != null) {
        if (n.children != null) throw Error(c(60));
        if (typeof n.dangerouslySetInnerHTML != "object" || !("__html" in n.dangerouslySetInnerHTML)) throw Error(c(61));
      }
      if (n.style != null && typeof n.style != "object") throw Error(c(62));
    }
  }
  function ei(e, n) {
    if (e.indexOf("-") === -1) return typeof n.is == "string";
    switch (e) {
      case "annotation-xml":
      case "color-profile":
      case "font-face":
      case "font-face-src":
      case "font-face-uri":
      case "font-face-format":
      case "font-face-name":
      case "missing-glyph":
        return !1;
      default:
        return !0;
    }
  }
  var ni = null;
  function ti(e) {
    return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
  }
  var ri = null, mt = null, vt = null;
  function us(e) {
    if (e = ar(e)) {
      if (typeof ri != "function") throw Error(c(280));
      var n = e.stateNode;
      n && (n = el(n), ri(e.stateNode, e.type, n));
    }
  }
  function as(e) {
    mt ? vt ? vt.push(e) : vt = [e] : mt = e;
  }
  function cs() {
    if (mt) {
      var e = mt, n = vt;
      if (vt = mt = null, us(e), n) for (e = 0; e < n.length; e++) us(n[e]);
    }
  }
  function ds(e, n) {
    return e(n);
  }
  function fs() {
  }
  var li = !1;
  function ps(e, n, t) {
    if (li) return e(n, t);
    li = !0;
    try {
      return ds(e, n, t);
    } finally {
      li = !1, (mt !== null || vt !== null) && (fs(), cs());
    }
  }
  function Ht(e, n) {
    var t = e.stateNode;
    if (t === null) return null;
    var r = el(t);
    if (r === null) return null;
    t = r[n];
    e: switch (n) {
      case "onClick":
      case "onClickCapture":
      case "onDoubleClick":
      case "onDoubleClickCapture":
      case "onMouseDown":
      case "onMouseDownCapture":
      case "onMouseMove":
      case "onMouseMoveCapture":
      case "onMouseUp":
      case "onMouseUpCapture":
      case "onMouseEnter":
        (r = !r.disabled) || (e = e.type, r = !(e === "button" || e === "input" || e === "select" || e === "textarea")), e = !r;
        break e;
      default:
        e = !1;
    }
    if (e) return null;
    if (t && typeof t != "function") throw Error(c(231, n, typeof t));
    return t;
  }
  var ii = !1;
  if (R) try {
    var Bt = {};
    Object.defineProperty(Bt, "passive", { get: function() {
      ii = !0;
    } }), window.addEventListener("test", Bt, Bt), window.removeEventListener("test", Bt, Bt);
  } catch {
    ii = !1;
  }
  function xc(e, n, t, r, l, i, s, d, f) {
    var y = Array.prototype.slice.call(arguments, 3);
    try {
      n.apply(t, y);
    } catch (N) {
      this.onError(N);
    }
  }
  var Xt = !1, Or = null, Fr = !1, oi = null, wc = { onError: function(e) {
    Xt = !0, Or = e;
  } };
  function kc(e, n, t, r, l, i, s, d, f) {
    Xt = !1, Or = null, xc.apply(wc, arguments);
  }
  function Sc(e, n, t, r, l, i, s, d, f) {
    if (kc.apply(this, arguments), Xt) {
      if (Xt) {
        var y = Or;
        Xt = !1, Or = null;
      } else throw Error(c(198));
      Fr || (Fr = !0, oi = y);
    }
  }
  function nt(e) {
    var n = e, t = e;
    if (e.alternate) for (; n.return; ) n = n.return;
    else {
      e = n;
      do
        n = e, (n.flags & 4098) !== 0 && (t = n.return), e = n.return;
      while (e);
    }
    return n.tag === 3 ? t : null;
  }
  function hs(e) {
    if (e.tag === 13) {
      var n = e.memoizedState;
      if (n === null && (e = e.alternate, e !== null && (n = e.memoizedState)), n !== null) return n.dehydrated;
    }
    return null;
  }
  function ms(e) {
    if (nt(e) !== e) throw Error(c(188));
  }
  function jc(e) {
    var n = e.alternate;
    if (!n) {
      if (n = nt(e), n === null) throw Error(c(188));
      return n !== e ? null : e;
    }
    for (var t = e, r = n; ; ) {
      var l = t.return;
      if (l === null) break;
      var i = l.alternate;
      if (i === null) {
        if (r = l.return, r !== null) {
          t = r;
          continue;
        }
        break;
      }
      if (l.child === i.child) {
        for (i = l.child; i; ) {
          if (i === t) return ms(l), e;
          if (i === r) return ms(l), n;
          i = i.sibling;
        }
        throw Error(c(188));
      }
      if (t.return !== r.return) t = l, r = i;
      else {
        for (var s = !1, d = l.child; d; ) {
          if (d === t) {
            s = !0, t = l, r = i;
            break;
          }
          if (d === r) {
            s = !0, r = l, t = i;
            break;
          }
          d = d.sibling;
        }
        if (!s) {
          for (d = i.child; d; ) {
            if (d === t) {
              s = !0, t = i, r = l;
              break;
            }
            if (d === r) {
              s = !0, r = i, t = l;
              break;
            }
            d = d.sibling;
          }
          if (!s) throw Error(c(189));
        }
      }
      if (t.alternate !== r) throw Error(c(190));
    }
    if (t.tag !== 3) throw Error(c(188));
    return t.stateNode.current === t ? e : n;
  }
  function vs(e) {
    return e = jc(e), e !== null ? gs(e) : null;
  }
  function gs(e) {
    if (e.tag === 5 || e.tag === 6) return e;
    for (e = e.child; e !== null; ) {
      var n = gs(e);
      if (n !== null) return n;
      e = e.sibling;
    }
    return null;
  }
  var ys = a.unstable_scheduleCallback, xs = a.unstable_cancelCallback, Nc = a.unstable_shouldYield, Cc = a.unstable_requestPaint, je = a.unstable_now, Ec = a.unstable_getCurrentPriorityLevel, si = a.unstable_ImmediatePriority, ws = a.unstable_UserBlockingPriority, Mr = a.unstable_NormalPriority, Rc = a.unstable_LowPriority, ks = a.unstable_IdlePriority, Ir = null, Sn = null;
  function zc(e) {
    if (Sn && typeof Sn.onCommitFiberRoot == "function") try {
      Sn.onCommitFiberRoot(Ir, e, void 0, (e.current.flags & 128) === 128);
    } catch {
    }
  }
  var hn = Math.clz32 ? Math.clz32 : Lc, Pc = Math.log, Tc = Math.LN2;
  function Lc(e) {
    return e >>>= 0, e === 0 ? 32 : 31 - (Pc(e) / Tc | 0) | 0;
  }
  var Wr = 64, Dr = 4194304;
  function Zt(e) {
    switch (e & -e) {
      case 1:
        return 1;
      case 2:
        return 2;
      case 4:
        return 4;
      case 8:
        return 8;
      case 16:
        return 16;
      case 32:
        return 32;
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return e & 4194240;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return e & 130023424;
      case 134217728:
        return 134217728;
      case 268435456:
        return 268435456;
      case 536870912:
        return 536870912;
      case 1073741824:
        return 1073741824;
      default:
        return e;
    }
  }
  function Vr(e, n) {
    var t = e.pendingLanes;
    if (t === 0) return 0;
    var r = 0, l = e.suspendedLanes, i = e.pingedLanes, s = t & 268435455;
    if (s !== 0) {
      var d = s & ~l;
      d !== 0 ? r = Zt(d) : (i &= s, i !== 0 && (r = Zt(i)));
    } else s = t & ~l, s !== 0 ? r = Zt(s) : i !== 0 && (r = Zt(i));
    if (r === 0) return 0;
    if (n !== 0 && n !== r && (n & l) === 0 && (l = r & -r, i = n & -n, l >= i || l === 16 && (i & 4194240) !== 0)) return n;
    if ((r & 4) !== 0 && (r |= t & 16), n = e.entangledLanes, n !== 0) for (e = e.entanglements, n &= r; 0 < n; ) t = 31 - hn(n), l = 1 << t, r |= e[t], n &= ~l;
    return r;
  }
  function Oc(e, n) {
    switch (e) {
      case 1:
      case 2:
      case 4:
        return n + 250;
      case 8:
      case 16:
      case 32:
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return n + 5e3;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return -1;
      case 134217728:
      case 268435456:
      case 536870912:
      case 1073741824:
        return -1;
      default:
        return -1;
    }
  }
  function Fc(e, n) {
    for (var t = e.suspendedLanes, r = e.pingedLanes, l = e.expirationTimes, i = e.pendingLanes; 0 < i; ) {
      var s = 31 - hn(i), d = 1 << s, f = l[s];
      f === -1 ? ((d & t) === 0 || (d & r) !== 0) && (l[s] = Oc(d, n)) : f <= n && (e.expiredLanes |= d), i &= ~d;
    }
  }
  function ui(e) {
    return e = e.pendingLanes & -1073741825, e !== 0 ? e : e & 1073741824 ? 1073741824 : 0;
  }
  function Ss() {
    var e = Wr;
    return Wr <<= 1, (Wr & 4194240) === 0 && (Wr = 64), e;
  }
  function ai(e) {
    for (var n = [], t = 0; 31 > t; t++) n.push(e);
    return n;
  }
  function Jt(e, n, t) {
    e.pendingLanes |= n, n !== 536870912 && (e.suspendedLanes = 0, e.pingedLanes = 0), e = e.eventTimes, n = 31 - hn(n), e[n] = t;
  }
  function Mc(e, n) {
    var t = e.pendingLanes & ~n;
    e.pendingLanes = n, e.suspendedLanes = 0, e.pingedLanes = 0, e.expiredLanes &= n, e.mutableReadLanes &= n, e.entangledLanes &= n, n = e.entanglements;
    var r = e.eventTimes;
    for (e = e.expirationTimes; 0 < t; ) {
      var l = 31 - hn(t), i = 1 << l;
      n[l] = 0, r[l] = -1, e[l] = -1, t &= ~i;
    }
  }
  function ci(e, n) {
    var t = e.entangledLanes |= n;
    for (e = e.entanglements; t; ) {
      var r = 31 - hn(t), l = 1 << r;
      l & n | e[r] & n && (e[r] |= n), t &= ~l;
    }
  }
  var ie = 0;
  function js(e) {
    return e &= -e, 1 < e ? 4 < e ? (e & 268435455) !== 0 ? 16 : 536870912 : 4 : 1;
  }
  var Ns, di, Cs, Es, Rs, fi = !1, Ur = [], Wn = null, Dn = null, Vn = null, Kt = /* @__PURE__ */ new Map(), Qt = /* @__PURE__ */ new Map(), Un = [], Ic = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
  function zs(e, n) {
    switch (e) {
      case "focusin":
      case "focusout":
        Wn = null;
        break;
      case "dragenter":
      case "dragleave":
        Dn = null;
        break;
      case "mouseover":
      case "mouseout":
        Vn = null;
        break;
      case "pointerover":
      case "pointerout":
        Kt.delete(n.pointerId);
        break;
      case "gotpointercapture":
      case "lostpointercapture":
        Qt.delete(n.pointerId);
    }
  }
  function Gt(e, n, t, r, l, i) {
    return e === null || e.nativeEvent !== i ? (e = { blockedOn: n, domEventName: t, eventSystemFlags: r, nativeEvent: i, targetContainers: [l] }, n !== null && (n = ar(n), n !== null && di(n)), e) : (e.eventSystemFlags |= r, n = e.targetContainers, l !== null && n.indexOf(l) === -1 && n.push(l), e);
  }
  function Wc(e, n, t, r, l) {
    switch (n) {
      case "focusin":
        return Wn = Gt(Wn, e, n, t, r, l), !0;
      case "dragenter":
        return Dn = Gt(Dn, e, n, t, r, l), !0;
      case "mouseover":
        return Vn = Gt(Vn, e, n, t, r, l), !0;
      case "pointerover":
        var i = l.pointerId;
        return Kt.set(i, Gt(Kt.get(i) || null, e, n, t, r, l)), !0;
      case "gotpointercapture":
        return i = l.pointerId, Qt.set(i, Gt(Qt.get(i) || null, e, n, t, r, l)), !0;
    }
    return !1;
  }
  function Ps(e) {
    var n = tt(e.target);
    if (n !== null) {
      var t = nt(n);
      if (t !== null) {
        if (n = t.tag, n === 13) {
          if (n = hs(t), n !== null) {
            e.blockedOn = n, Rs(e.priority, function() {
              Cs(t);
            });
            return;
          }
        } else if (n === 3 && t.stateNode.current.memoizedState.isDehydrated) {
          e.blockedOn = t.tag === 3 ? t.stateNode.containerInfo : null;
          return;
        }
      }
    }
    e.blockedOn = null;
  }
  function qr(e) {
    if (e.blockedOn !== null) return !1;
    for (var n = e.targetContainers; 0 < n.length; ) {
      var t = hi(e.domEventName, e.eventSystemFlags, n[0], e.nativeEvent);
      if (t === null) {
        t = e.nativeEvent;
        var r = new t.constructor(t.type, t);
        ni = r, t.target.dispatchEvent(r), ni = null;
      } else return n = ar(t), n !== null && di(n), e.blockedOn = t, !1;
      n.shift();
    }
    return !0;
  }
  function Ts(e, n, t) {
    qr(e) && t.delete(n);
  }
  function Dc() {
    fi = !1, Wn !== null && qr(Wn) && (Wn = null), Dn !== null && qr(Dn) && (Dn = null), Vn !== null && qr(Vn) && (Vn = null), Kt.forEach(Ts), Qt.forEach(Ts);
  }
  function Yt(e, n) {
    e.blockedOn === n && (e.blockedOn = null, fi || (fi = !0, a.unstable_scheduleCallback(a.unstable_NormalPriority, Dc)));
  }
  function bt(e) {
    function n(l) {
      return Yt(l, e);
    }
    if (0 < Ur.length) {
      Yt(Ur[0], e);
      for (var t = 1; t < Ur.length; t++) {
        var r = Ur[t];
        r.blockedOn === e && (r.blockedOn = null);
      }
    }
    for (Wn !== null && Yt(Wn, e), Dn !== null && Yt(Dn, e), Vn !== null && Yt(Vn, e), Kt.forEach(n), Qt.forEach(n), t = 0; t < Un.length; t++) r = Un[t], r.blockedOn === e && (r.blockedOn = null);
    for (; 0 < Un.length && (t = Un[0], t.blockedOn === null); ) Ps(t), t.blockedOn === null && Un.shift();
  }
  var gt = ve.ReactCurrentBatchConfig, Ar = !0;
  function Vc(e, n, t, r) {
    var l = ie, i = gt.transition;
    gt.transition = null;
    try {
      ie = 1, pi(e, n, t, r);
    } finally {
      ie = l, gt.transition = i;
    }
  }
  function Uc(e, n, t, r) {
    var l = ie, i = gt.transition;
    gt.transition = null;
    try {
      ie = 4, pi(e, n, t, r);
    } finally {
      ie = l, gt.transition = i;
    }
  }
  function pi(e, n, t, r) {
    if (Ar) {
      var l = hi(e, n, t, r);
      if (l === null) Li(e, n, r, Hr, t), zs(e, r);
      else if (Wc(l, e, n, t, r)) r.stopPropagation();
      else if (zs(e, r), n & 4 && -1 < Ic.indexOf(e)) {
        for (; l !== null; ) {
          var i = ar(l);
          if (i !== null && Ns(i), i = hi(e, n, t, r), i === null && Li(e, n, r, Hr, t), i === l) break;
          l = i;
        }
        l !== null && r.stopPropagation();
      } else Li(e, n, r, null, t);
    }
  }
  var Hr = null;
  function hi(e, n, t, r) {
    if (Hr = null, e = ti(r), e = tt(e), e !== null) if (n = nt(e), n === null) e = null;
    else if (t = n.tag, t === 13) {
      if (e = hs(n), e !== null) return e;
      e = null;
    } else if (t === 3) {
      if (n.stateNode.current.memoizedState.isDehydrated) return n.tag === 3 ? n.stateNode.containerInfo : null;
      e = null;
    } else n !== e && (e = null);
    return Hr = e, null;
  }
  function Ls(e) {
    switch (e) {
      case "cancel":
      case "click":
      case "close":
      case "contextmenu":
      case "copy":
      case "cut":
      case "auxclick":
      case "dblclick":
      case "dragend":
      case "dragstart":
      case "drop":
      case "focusin":
      case "focusout":
      case "input":
      case "invalid":
      case "keydown":
      case "keypress":
      case "keyup":
      case "mousedown":
      case "mouseup":
      case "paste":
      case "pause":
      case "play":
      case "pointercancel":
      case "pointerdown":
      case "pointerup":
      case "ratechange":
      case "reset":
      case "resize":
      case "seeked":
      case "submit":
      case "touchcancel":
      case "touchend":
      case "touchstart":
      case "volumechange":
      case "change":
      case "selectionchange":
      case "textInput":
      case "compositionstart":
      case "compositionend":
      case "compositionupdate":
      case "beforeblur":
      case "afterblur":
      case "beforeinput":
      case "blur":
      case "fullscreenchange":
      case "focus":
      case "hashchange":
      case "popstate":
      case "select":
      case "selectstart":
        return 1;
      case "drag":
      case "dragenter":
      case "dragexit":
      case "dragleave":
      case "dragover":
      case "mousemove":
      case "mouseout":
      case "mouseover":
      case "pointermove":
      case "pointerout":
      case "pointerover":
      case "scroll":
      case "toggle":
      case "touchmove":
      case "wheel":
      case "mouseenter":
      case "mouseleave":
      case "pointerenter":
      case "pointerleave":
        return 4;
      case "message":
        switch (Ec()) {
          case si:
            return 1;
          case ws:
            return 4;
          case Mr:
          case Rc:
            return 16;
          case ks:
            return 536870912;
          default:
            return 16;
        }
      default:
        return 16;
    }
  }
  var qn = null, mi = null, Br = null;
  function Os() {
    if (Br) return Br;
    var e, n = mi, t = n.length, r, l = "value" in qn ? qn.value : qn.textContent, i = l.length;
    for (e = 0; e < t && n[e] === l[e]; e++) ;
    var s = t - e;
    for (r = 1; r <= s && n[t - r] === l[i - r]; r++) ;
    return Br = l.slice(e, 1 < r ? 1 - r : void 0);
  }
  function Xr(e) {
    var n = e.keyCode;
    return "charCode" in e ? (e = e.charCode, e === 0 && n === 13 && (e = 13)) : e = n, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
  }
  function Zr() {
    return !0;
  }
  function Fs() {
    return !1;
  }
  function rn(e) {
    function n(t, r, l, i, s) {
      this._reactName = t, this._targetInst = l, this.type = r, this.nativeEvent = i, this.target = s, this.currentTarget = null;
      for (var d in e) e.hasOwnProperty(d) && (t = e[d], this[d] = t ? t(i) : i[d]);
      return this.isDefaultPrevented = (i.defaultPrevented != null ? i.defaultPrevented : i.returnValue === !1) ? Zr : Fs, this.isPropagationStopped = Fs, this;
    }
    return P(n.prototype, { preventDefault: function() {
      this.defaultPrevented = !0;
      var t = this.nativeEvent;
      t && (t.preventDefault ? t.preventDefault() : typeof t.returnValue != "unknown" && (t.returnValue = !1), this.isDefaultPrevented = Zr);
    }, stopPropagation: function() {
      var t = this.nativeEvent;
      t && (t.stopPropagation ? t.stopPropagation() : typeof t.cancelBubble != "unknown" && (t.cancelBubble = !0), this.isPropagationStopped = Zr);
    }, persist: function() {
    }, isPersistent: Zr }), n;
  }
  var yt = { eventPhase: 0, bubbles: 0, cancelable: 0, timeStamp: function(e) {
    return e.timeStamp || Date.now();
  }, defaultPrevented: 0, isTrusted: 0 }, vi = rn(yt), _t = P({}, yt, { view: 0, detail: 0 }), qc = rn(_t), gi, yi, $t, Jr = P({}, _t, { screenX: 0, screenY: 0, clientX: 0, clientY: 0, pageX: 0, pageY: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, getModifierState: wi, button: 0, buttons: 0, relatedTarget: function(e) {
    return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
  }, movementX: function(e) {
    return "movementX" in e ? e.movementX : (e !== $t && ($t && e.type === "mousemove" ? (gi = e.screenX - $t.screenX, yi = e.screenY - $t.screenY) : yi = gi = 0, $t = e), gi);
  }, movementY: function(e) {
    return "movementY" in e ? e.movementY : yi;
  } }), Ms = rn(Jr), Ac = P({}, Jr, { dataTransfer: 0 }), Hc = rn(Ac), Bc = P({}, _t, { relatedTarget: 0 }), xi = rn(Bc), Xc = P({}, yt, { animationName: 0, elapsedTime: 0, pseudoElement: 0 }), Zc = rn(Xc), Jc = P({}, yt, { clipboardData: function(e) {
    return "clipboardData" in e ? e.clipboardData : window.clipboardData;
  } }), Kc = rn(Jc), Qc = P({}, yt, { data: 0 }), Is = rn(Qc), Gc = {
    Esc: "Escape",
    Spacebar: " ",
    Left: "ArrowLeft",
    Up: "ArrowUp",
    Right: "ArrowRight",
    Down: "ArrowDown",
    Del: "Delete",
    Win: "OS",
    Menu: "ContextMenu",
    Apps: "ContextMenu",
    Scroll: "ScrollLock",
    MozPrintableKey: "Unidentified"
  }, Yc = {
    8: "Backspace",
    9: "Tab",
    12: "Clear",
    13: "Enter",
    16: "Shift",
    17: "Control",
    18: "Alt",
    19: "Pause",
    20: "CapsLock",
    27: "Escape",
    32: " ",
    33: "PageUp",
    34: "PageDown",
    35: "End",
    36: "Home",
    37: "ArrowLeft",
    38: "ArrowUp",
    39: "ArrowRight",
    40: "ArrowDown",
    45: "Insert",
    46: "Delete",
    112: "F1",
    113: "F2",
    114: "F3",
    115: "F4",
    116: "F5",
    117: "F6",
    118: "F7",
    119: "F8",
    120: "F9",
    121: "F10",
    122: "F11",
    123: "F12",
    144: "NumLock",
    145: "ScrollLock",
    224: "Meta"
  }, bc = { Alt: "altKey", Control: "ctrlKey", Meta: "metaKey", Shift: "shiftKey" };
  function _c(e) {
    var n = this.nativeEvent;
    return n.getModifierState ? n.getModifierState(e) : (e = bc[e]) ? !!n[e] : !1;
  }
  function wi() {
    return _c;
  }
  var $c = P({}, _t, { key: function(e) {
    if (e.key) {
      var n = Gc[e.key] || e.key;
      if (n !== "Unidentified") return n;
    }
    return e.type === "keypress" ? (e = Xr(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? Yc[e.keyCode] || "Unidentified" : "";
  }, code: 0, location: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, repeat: 0, locale: 0, getModifierState: wi, charCode: function(e) {
    return e.type === "keypress" ? Xr(e) : 0;
  }, keyCode: function(e) {
    return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
  }, which: function(e) {
    return e.type === "keypress" ? Xr(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
  } }), ed = rn($c), nd = P({}, Jr, { pointerId: 0, width: 0, height: 0, pressure: 0, tangentialPressure: 0, tiltX: 0, tiltY: 0, twist: 0, pointerType: 0, isPrimary: 0 }), Ws = rn(nd), td = P({}, _t, { touches: 0, targetTouches: 0, changedTouches: 0, altKey: 0, metaKey: 0, ctrlKey: 0, shiftKey: 0, getModifierState: wi }), rd = rn(td), ld = P({}, yt, { propertyName: 0, elapsedTime: 0, pseudoElement: 0 }), id = rn(ld), od = P({}, Jr, {
    deltaX: function(e) {
      return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
    },
    deltaY: function(e) {
      return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
    },
    deltaZ: 0,
    deltaMode: 0
  }), sd = rn(od), ud = [9, 13, 27, 32], ki = R && "CompositionEvent" in window, er = null;
  R && "documentMode" in document && (er = document.documentMode);
  var ad = R && "TextEvent" in window && !er, Ds = R && (!ki || er && 8 < er && 11 >= er), Vs = " ", Us = !1;
  function qs(e, n) {
    switch (e) {
      case "keyup":
        return ud.indexOf(n.keyCode) !== -1;
      case "keydown":
        return n.keyCode !== 229;
      case "keypress":
      case "mousedown":
      case "focusout":
        return !0;
      default:
        return !1;
    }
  }
  function As(e) {
    return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
  }
  var xt = !1;
  function cd(e, n) {
    switch (e) {
      case "compositionend":
        return As(n);
      case "keypress":
        return n.which !== 32 ? null : (Us = !0, Vs);
      case "textInput":
        return e = n.data, e === Vs && Us ? null : e;
      default:
        return null;
    }
  }
  function dd(e, n) {
    if (xt) return e === "compositionend" || !ki && qs(e, n) ? (e = Os(), Br = mi = qn = null, xt = !1, e) : null;
    switch (e) {
      case "paste":
        return null;
      case "keypress":
        if (!(n.ctrlKey || n.altKey || n.metaKey) || n.ctrlKey && n.altKey) {
          if (n.char && 1 < n.char.length) return n.char;
          if (n.which) return String.fromCharCode(n.which);
        }
        return null;
      case "compositionend":
        return Ds && n.locale !== "ko" ? null : n.data;
      default:
        return null;
    }
  }
  var fd = { color: !0, date: !0, datetime: !0, "datetime-local": !0, email: !0, month: !0, number: !0, password: !0, range: !0, search: !0, tel: !0, text: !0, time: !0, url: !0, week: !0 };
  function Hs(e) {
    var n = e && e.nodeName && e.nodeName.toLowerCase();
    return n === "input" ? !!fd[e.type] : n === "textarea";
  }
  function Bs(e, n, t, r) {
    as(r), n = br(n, "onChange"), 0 < n.length && (t = new vi("onChange", "change", null, t, r), e.push({ event: t, listeners: n }));
  }
  var nr = null, tr = null;
  function pd(e) {
    su(e, 0);
  }
  function Kr(e) {
    var n = Nt(e);
    if (bo(n)) return e;
  }
  function hd(e, n) {
    if (e === "change") return n;
  }
  var Xs = !1;
  if (R) {
    var Si;
    if (R) {
      var ji = "oninput" in document;
      if (!ji) {
        var Zs = document.createElement("div");
        Zs.setAttribute("oninput", "return;"), ji = typeof Zs.oninput == "function";
      }
      Si = ji;
    } else Si = !1;
    Xs = Si && (!document.documentMode || 9 < document.documentMode);
  }
  function Js() {
    nr && (nr.detachEvent("onpropertychange", Ks), tr = nr = null);
  }
  function Ks(e) {
    if (e.propertyName === "value" && Kr(tr)) {
      var n = [];
      Bs(n, tr, e, ti(e)), ps(pd, n);
    }
  }
  function md(e, n, t) {
    e === "focusin" ? (Js(), nr = n, tr = t, nr.attachEvent("onpropertychange", Ks)) : e === "focusout" && Js();
  }
  function vd(e) {
    if (e === "selectionchange" || e === "keyup" || e === "keydown") return Kr(tr);
  }
  function gd(e, n) {
    if (e === "click") return Kr(n);
  }
  function yd(e, n) {
    if (e === "input" || e === "change") return Kr(n);
  }
  function xd(e, n) {
    return e === n && (e !== 0 || 1 / e === 1 / n) || e !== e && n !== n;
  }
  var mn = typeof Object.is == "function" ? Object.is : xd;
  function rr(e, n) {
    if (mn(e, n)) return !0;
    if (typeof e != "object" || e === null || typeof n != "object" || n === null) return !1;
    var t = Object.keys(e), r = Object.keys(n);
    if (t.length !== r.length) return !1;
    for (r = 0; r < t.length; r++) {
      var l = t[r];
      if (!T.call(n, l) || !mn(e[l], n[l])) return !1;
    }
    return !0;
  }
  function Qs(e) {
    for (; e && e.firstChild; ) e = e.firstChild;
    return e;
  }
  function Gs(e, n) {
    var t = Qs(e);
    e = 0;
    for (var r; t; ) {
      if (t.nodeType === 3) {
        if (r = e + t.textContent.length, e <= n && r >= n) return { node: t, offset: n - e };
        e = r;
      }
      e: {
        for (; t; ) {
          if (t.nextSibling) {
            t = t.nextSibling;
            break e;
          }
          t = t.parentNode;
        }
        t = void 0;
      }
      t = Qs(t);
    }
  }
  function Ys(e, n) {
    return e && n ? e === n ? !0 : e && e.nodeType === 3 ? !1 : n && n.nodeType === 3 ? Ys(e, n.parentNode) : "contains" in e ? e.contains(n) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(n) & 16) : !1 : !1;
  }
  function bs() {
    for (var e = window, n = Tr(); n instanceof e.HTMLIFrameElement; ) {
      try {
        var t = typeof n.contentWindow.location.href == "string";
      } catch {
        t = !1;
      }
      if (t) e = n.contentWindow;
      else break;
      n = Tr(e.document);
    }
    return n;
  }
  function Ni(e) {
    var n = e && e.nodeName && e.nodeName.toLowerCase();
    return n && (n === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || n === "textarea" || e.contentEditable === "true");
  }
  function wd(e) {
    var n = bs(), t = e.focusedElem, r = e.selectionRange;
    if (n !== t && t && t.ownerDocument && Ys(t.ownerDocument.documentElement, t)) {
      if (r !== null && Ni(t)) {
        if (n = r.start, e = r.end, e === void 0 && (e = n), "selectionStart" in t) t.selectionStart = n, t.selectionEnd = Math.min(e, t.value.length);
        else if (e = (n = t.ownerDocument || document) && n.defaultView || window, e.getSelection) {
          e = e.getSelection();
          var l = t.textContent.length, i = Math.min(r.start, l);
          r = r.end === void 0 ? i : Math.min(r.end, l), !e.extend && i > r && (l = r, r = i, i = l), l = Gs(t, i);
          var s = Gs(
            t,
            r
          );
          l && s && (e.rangeCount !== 1 || e.anchorNode !== l.node || e.anchorOffset !== l.offset || e.focusNode !== s.node || e.focusOffset !== s.offset) && (n = n.createRange(), n.setStart(l.node, l.offset), e.removeAllRanges(), i > r ? (e.addRange(n), e.extend(s.node, s.offset)) : (n.setEnd(s.node, s.offset), e.addRange(n)));
        }
      }
      for (n = [], e = t; e = e.parentNode; ) e.nodeType === 1 && n.push({ element: e, left: e.scrollLeft, top: e.scrollTop });
      for (typeof t.focus == "function" && t.focus(), t = 0; t < n.length; t++) e = n[t], e.element.scrollLeft = e.left, e.element.scrollTop = e.top;
    }
  }
  var kd = R && "documentMode" in document && 11 >= document.documentMode, wt = null, Ci = null, lr = null, Ei = !1;
  function _s(e, n, t) {
    var r = t.window === t ? t.document : t.nodeType === 9 ? t : t.ownerDocument;
    Ei || wt == null || wt !== Tr(r) || (r = wt, "selectionStart" in r && Ni(r) ? r = { start: r.selectionStart, end: r.selectionEnd } : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = { anchorNode: r.anchorNode, anchorOffset: r.anchorOffset, focusNode: r.focusNode, focusOffset: r.focusOffset }), lr && rr(lr, r) || (lr = r, r = br(Ci, "onSelect"), 0 < r.length && (n = new vi("onSelect", "select", null, n, t), e.push({ event: n, listeners: r }), n.target = wt)));
  }
  function Qr(e, n) {
    var t = {};
    return t[e.toLowerCase()] = n.toLowerCase(), t["Webkit" + e] = "webkit" + n, t["Moz" + e] = "moz" + n, t;
  }
  var kt = { animationend: Qr("Animation", "AnimationEnd"), animationiteration: Qr("Animation", "AnimationIteration"), animationstart: Qr("Animation", "AnimationStart"), transitionend: Qr("Transition", "TransitionEnd") }, Ri = {}, $s = {};
  R && ($s = document.createElement("div").style, "AnimationEvent" in window || (delete kt.animationend.animation, delete kt.animationiteration.animation, delete kt.animationstart.animation), "TransitionEvent" in window || delete kt.transitionend.transition);
  function Gr(e) {
    if (Ri[e]) return Ri[e];
    if (!kt[e]) return e;
    var n = kt[e], t;
    for (t in n) if (n.hasOwnProperty(t) && t in $s) return Ri[e] = n[t];
    return e;
  }
  var eu = Gr("animationend"), nu = Gr("animationiteration"), tu = Gr("animationstart"), ru = Gr("transitionend"), lu = /* @__PURE__ */ new Map(), iu = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
  function An(e, n) {
    lu.set(e, n), v(n, [e]);
  }
  for (var zi = 0; zi < iu.length; zi++) {
    var Pi = iu[zi], Sd = Pi.toLowerCase(), jd = Pi[0].toUpperCase() + Pi.slice(1);
    An(Sd, "on" + jd);
  }
  An(eu, "onAnimationEnd"), An(nu, "onAnimationIteration"), An(tu, "onAnimationStart"), An("dblclick", "onDoubleClick"), An("focusin", "onFocus"), An("focusout", "onBlur"), An(ru, "onTransitionEnd"), E("onMouseEnter", ["mouseout", "mouseover"]), E("onMouseLeave", ["mouseout", "mouseover"]), E("onPointerEnter", ["pointerout", "pointerover"]), E("onPointerLeave", ["pointerout", "pointerover"]), v("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), v("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), v("onBeforeInput", ["compositionend", "keypress", "textInput", "paste"]), v("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), v("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), v("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
  var ir = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), Nd = new Set("cancel close invalid load scroll toggle".split(" ").concat(ir));
  function ou(e, n, t) {
    var r = e.type || "unknown-event";
    e.currentTarget = t, Sc(r, n, void 0, e), e.currentTarget = null;
  }
  function su(e, n) {
    n = (n & 4) !== 0;
    for (var t = 0; t < e.length; t++) {
      var r = e[t], l = r.event;
      r = r.listeners;
      e: {
        var i = void 0;
        if (n) for (var s = r.length - 1; 0 <= s; s--) {
          var d = r[s], f = d.instance, y = d.currentTarget;
          if (d = d.listener, f !== i && l.isPropagationStopped()) break e;
          ou(l, d, y), i = f;
        }
        else for (s = 0; s < r.length; s++) {
          if (d = r[s], f = d.instance, y = d.currentTarget, d = d.listener, f !== i && l.isPropagationStopped()) break e;
          ou(l, d, y), i = f;
        }
      }
    }
    if (Fr) throw e = oi, Fr = !1, oi = null, e;
  }
  function ce(e, n) {
    var t = n[Di];
    t === void 0 && (t = n[Di] = /* @__PURE__ */ new Set());
    var r = e + "__bubble";
    t.has(r) || (uu(n, e, 2, !1), t.add(r));
  }
  function Ti(e, n, t) {
    var r = 0;
    n && (r |= 4), uu(t, e, r, n);
  }
  var Yr = "_reactListening" + Math.random().toString(36).slice(2);
  function or(e) {
    if (!e[Yr]) {
      e[Yr] = !0, x.forEach(function(t) {
        t !== "selectionchange" && (Nd.has(t) || Ti(t, !1, e), Ti(t, !0, e));
      });
      var n = e.nodeType === 9 ? e : e.ownerDocument;
      n === null || n[Yr] || (n[Yr] = !0, Ti("selectionchange", !1, n));
    }
  }
  function uu(e, n, t, r) {
    switch (Ls(n)) {
      case 1:
        var l = Vc;
        break;
      case 4:
        l = Uc;
        break;
      default:
        l = pi;
    }
    t = l.bind(null, n, t, e), l = void 0, !ii || n !== "touchstart" && n !== "touchmove" && n !== "wheel" || (l = !0), r ? l !== void 0 ? e.addEventListener(n, t, { capture: !0, passive: l }) : e.addEventListener(n, t, !0) : l !== void 0 ? e.addEventListener(n, t, { passive: l }) : e.addEventListener(n, t, !1);
  }
  function Li(e, n, t, r, l) {
    var i = r;
    if ((n & 1) === 0 && (n & 2) === 0 && r !== null) e: for (; ; ) {
      if (r === null) return;
      var s = r.tag;
      if (s === 3 || s === 4) {
        var d = r.stateNode.containerInfo;
        if (d === l || d.nodeType === 8 && d.parentNode === l) break;
        if (s === 4) for (s = r.return; s !== null; ) {
          var f = s.tag;
          if ((f === 3 || f === 4) && (f = s.stateNode.containerInfo, f === l || f.nodeType === 8 && f.parentNode === l)) return;
          s = s.return;
        }
        for (; d !== null; ) {
          if (s = tt(d), s === null) return;
          if (f = s.tag, f === 5 || f === 6) {
            r = i = s;
            continue e;
          }
          d = d.parentNode;
        }
      }
      r = r.return;
    }
    ps(function() {
      var y = i, N = ti(t), C = [];
      e: {
        var j = lu.get(e);
        if (j !== void 0) {
          var F = vi, W = e;
          switch (e) {
            case "keypress":
              if (Xr(t) === 0) break e;
            case "keydown":
            case "keyup":
              F = ed;
              break;
            case "focusin":
              W = "focus", F = xi;
              break;
            case "focusout":
              W = "blur", F = xi;
              break;
            case "beforeblur":
            case "afterblur":
              F = xi;
              break;
            case "click":
              if (t.button === 2) break e;
            case "auxclick":
            case "dblclick":
            case "mousedown":
            case "mousemove":
            case "mouseup":
            case "mouseout":
            case "mouseover":
            case "contextmenu":
              F = Ms;
              break;
            case "drag":
            case "dragend":
            case "dragenter":
            case "dragexit":
            case "dragleave":
            case "dragover":
            case "dragstart":
            case "drop":
              F = Hc;
              break;
            case "touchcancel":
            case "touchend":
            case "touchmove":
            case "touchstart":
              F = rd;
              break;
            case eu:
            case nu:
            case tu:
              F = Zc;
              break;
            case ru:
              F = id;
              break;
            case "scroll":
              F = qc;
              break;
            case "wheel":
              F = sd;
              break;
            case "copy":
            case "cut":
            case "paste":
              F = Kc;
              break;
            case "gotpointercapture":
            case "lostpointercapture":
            case "pointercancel":
            case "pointerdown":
            case "pointermove":
            case "pointerout":
            case "pointerover":
            case "pointerup":
              F = Ws;
          }
          var D = (n & 4) !== 0, Ne = !D && e === "scroll", m = D ? j !== null ? j + "Capture" : null : j;
          D = [];
          for (var p = y, g; p !== null; ) {
            g = p;
            var L = g.stateNode;
            if (g.tag === 5 && L !== null && (g = L, m !== null && (L = Ht(p, m), L != null && D.push(sr(p, L, g)))), Ne) break;
            p = p.return;
          }
          0 < D.length && (j = new F(j, W, null, t, N), C.push({ event: j, listeners: D }));
        }
      }
      if ((n & 7) === 0) {
        e: {
          if (j = e === "mouseover" || e === "pointerover", F = e === "mouseout" || e === "pointerout", j && t !== ni && (W = t.relatedTarget || t.fromElement) && (tt(W) || W[zn])) break e;
          if ((F || j) && (j = N.window === N ? N : (j = N.ownerDocument) ? j.defaultView || j.parentWindow : window, F ? (W = t.relatedTarget || t.toElement, F = y, W = W ? tt(W) : null, W !== null && (Ne = nt(W), W !== Ne || W.tag !== 5 && W.tag !== 6) && (W = null)) : (F = null, W = y), F !== W)) {
            if (D = Ms, L = "onMouseLeave", m = "onMouseEnter", p = "mouse", (e === "pointerout" || e === "pointerover") && (D = Ws, L = "onPointerLeave", m = "onPointerEnter", p = "pointer"), Ne = F == null ? j : Nt(F), g = W == null ? j : Nt(W), j = new D(L, p + "leave", F, t, N), j.target = Ne, j.relatedTarget = g, L = null, tt(N) === y && (D = new D(m, p + "enter", W, t, N), D.target = g, D.relatedTarget = Ne, L = D), Ne = L, F && W) n: {
              for (D = F, m = W, p = 0, g = D; g; g = St(g)) p++;
              for (g = 0, L = m; L; L = St(L)) g++;
              for (; 0 < p - g; ) D = St(D), p--;
              for (; 0 < g - p; ) m = St(m), g--;
              for (; p--; ) {
                if (D === m || m !== null && D === m.alternate) break n;
                D = St(D), m = St(m);
              }
              D = null;
            }
            else D = null;
            F !== null && au(C, j, F, D, !1), W !== null && Ne !== null && au(C, Ne, W, D, !0);
          }
        }
        e: {
          if (j = y ? Nt(y) : window, F = j.nodeName && j.nodeName.toLowerCase(), F === "select" || F === "input" && j.type === "file") var V = hd;
          else if (Hs(j)) if (Xs) V = yd;
          else {
            V = vd;
            var A = md;
          }
          else (F = j.nodeName) && F.toLowerCase() === "input" && (j.type === "checkbox" || j.type === "radio") && (V = gd);
          if (V && (V = V(e, y))) {
            Bs(C, V, t, N);
            break e;
          }
          A && A(e, j, y), e === "focusout" && (A = j._wrapperState) && A.controlled && j.type === "number" && Yl(j, "number", j.value);
        }
        switch (A = y ? Nt(y) : window, e) {
          case "focusin":
            (Hs(A) || A.contentEditable === "true") && (wt = A, Ci = y, lr = null);
            break;
          case "focusout":
            lr = Ci = wt = null;
            break;
          case "mousedown":
            Ei = !0;
            break;
          case "contextmenu":
          case "mouseup":
          case "dragend":
            Ei = !1, _s(C, t, N);
            break;
          case "selectionchange":
            if (kd) break;
          case "keydown":
          case "keyup":
            _s(C, t, N);
        }
        var H;
        if (ki) e: {
          switch (e) {
            case "compositionstart":
              var B = "onCompositionStart";
              break e;
            case "compositionend":
              B = "onCompositionEnd";
              break e;
            case "compositionupdate":
              B = "onCompositionUpdate";
              break e;
          }
          B = void 0;
        }
        else xt ? qs(e, t) && (B = "onCompositionEnd") : e === "keydown" && t.keyCode === 229 && (B = "onCompositionStart");
        B && (Ds && t.locale !== "ko" && (xt || B !== "onCompositionStart" ? B === "onCompositionEnd" && xt && (H = Os()) : (qn = N, mi = "value" in qn ? qn.value : qn.textContent, xt = !0)), A = br(y, B), 0 < A.length && (B = new Is(B, e, null, t, N), C.push({ event: B, listeners: A }), H ? B.data = H : (H = As(t), H !== null && (B.data = H)))), (H = ad ? cd(e, t) : dd(e, t)) && (y = br(y, "onBeforeInput"), 0 < y.length && (N = new Is("onBeforeInput", "beforeinput", null, t, N), C.push({ event: N, listeners: y }), N.data = H));
      }
      su(C, n);
    });
  }
  function sr(e, n, t) {
    return { instance: e, listener: n, currentTarget: t };
  }
  function br(e, n) {
    for (var t = n + "Capture", r = []; e !== null; ) {
      var l = e, i = l.stateNode;
      l.tag === 5 && i !== null && (l = i, i = Ht(e, t), i != null && r.unshift(sr(e, i, l)), i = Ht(e, n), i != null && r.push(sr(e, i, l))), e = e.return;
    }
    return r;
  }
  function St(e) {
    if (e === null) return null;
    do
      e = e.return;
    while (e && e.tag !== 5);
    return e || null;
  }
  function au(e, n, t, r, l) {
    for (var i = n._reactName, s = []; t !== null && t !== r; ) {
      var d = t, f = d.alternate, y = d.stateNode;
      if (f !== null && f === r) break;
      d.tag === 5 && y !== null && (d = y, l ? (f = Ht(t, i), f != null && s.unshift(sr(t, f, d))) : l || (f = Ht(t, i), f != null && s.push(sr(t, f, d)))), t = t.return;
    }
    s.length !== 0 && e.push({ event: n, listeners: s });
  }
  var Cd = /\r\n?/g, Ed = /\u0000|\uFFFD/g;
  function cu(e) {
    return (typeof e == "string" ? e : "" + e).replace(Cd, `
`).replace(Ed, "");
  }
  function _r(e, n, t) {
    if (n = cu(n), cu(e) !== n && t) throw Error(c(425));
  }
  function $r() {
  }
  var Oi = null, Fi = null;
  function Mi(e, n) {
    return e === "textarea" || e === "noscript" || typeof n.children == "string" || typeof n.children == "number" || typeof n.dangerouslySetInnerHTML == "object" && n.dangerouslySetInnerHTML !== null && n.dangerouslySetInnerHTML.__html != null;
  }
  var Ii = typeof setTimeout == "function" ? setTimeout : void 0, Rd = typeof clearTimeout == "function" ? clearTimeout : void 0, du = typeof Promise == "function" ? Promise : void 0, zd = typeof queueMicrotask == "function" ? queueMicrotask : typeof du < "u" ? function(e) {
    return du.resolve(null).then(e).catch(Pd);
  } : Ii;
  function Pd(e) {
    setTimeout(function() {
      throw e;
    });
  }
  function Wi(e, n) {
    var t = n, r = 0;
    do {
      var l = t.nextSibling;
      if (e.removeChild(t), l && l.nodeType === 8) if (t = l.data, t === "/$") {
        if (r === 0) {
          e.removeChild(l), bt(n);
          return;
        }
        r--;
      } else t !== "$" && t !== "$?" && t !== "$!" || r++;
      t = l;
    } while (t);
    bt(n);
  }
  function Hn(e) {
    for (; e != null; e = e.nextSibling) {
      var n = e.nodeType;
      if (n === 1 || n === 3) break;
      if (n === 8) {
        if (n = e.data, n === "$" || n === "$!" || n === "$?") break;
        if (n === "/$") return null;
      }
    }
    return e;
  }
  function fu(e) {
    e = e.previousSibling;
    for (var n = 0; e; ) {
      if (e.nodeType === 8) {
        var t = e.data;
        if (t === "$" || t === "$!" || t === "$?") {
          if (n === 0) return e;
          n--;
        } else t === "/$" && n++;
      }
      e = e.previousSibling;
    }
    return null;
  }
  var jt = Math.random().toString(36).slice(2), jn = "__reactFiber$" + jt, ur = "__reactProps$" + jt, zn = "__reactContainer$" + jt, Di = "__reactEvents$" + jt, Td = "__reactListeners$" + jt, Ld = "__reactHandles$" + jt;
  function tt(e) {
    var n = e[jn];
    if (n) return n;
    for (var t = e.parentNode; t; ) {
      if (n = t[zn] || t[jn]) {
        if (t = n.alternate, n.child !== null || t !== null && t.child !== null) for (e = fu(e); e !== null; ) {
          if (t = e[jn]) return t;
          e = fu(e);
        }
        return n;
      }
      e = t, t = e.parentNode;
    }
    return null;
  }
  function ar(e) {
    return e = e[jn] || e[zn], !e || e.tag !== 5 && e.tag !== 6 && e.tag !== 13 && e.tag !== 3 ? null : e;
  }
  function Nt(e) {
    if (e.tag === 5 || e.tag === 6) return e.stateNode;
    throw Error(c(33));
  }
  function el(e) {
    return e[ur] || null;
  }
  var Vi = [], Ct = -1;
  function Bn(e) {
    return { current: e };
  }
  function de(e) {
    0 > Ct || (e.current = Vi[Ct], Vi[Ct] = null, Ct--);
  }
  function ae(e, n) {
    Ct++, Vi[Ct] = e.current, e.current = n;
  }
  var Xn = {}, Be = Bn(Xn), Ge = Bn(!1), rt = Xn;
  function Et(e, n) {
    var t = e.type.contextTypes;
    if (!t) return Xn;
    var r = e.stateNode;
    if (r && r.__reactInternalMemoizedUnmaskedChildContext === n) return r.__reactInternalMemoizedMaskedChildContext;
    var l = {}, i;
    for (i in t) l[i] = n[i];
    return r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = n, e.__reactInternalMemoizedMaskedChildContext = l), l;
  }
  function Ye(e) {
    return e = e.childContextTypes, e != null;
  }
  function nl() {
    de(Ge), de(Be);
  }
  function pu(e, n, t) {
    if (Be.current !== Xn) throw Error(c(168));
    ae(Be, n), ae(Ge, t);
  }
  function hu(e, n, t) {
    var r = e.stateNode;
    if (n = n.childContextTypes, typeof r.getChildContext != "function") return t;
    r = r.getChildContext();
    for (var l in r) if (!(l in n)) throw Error(c(108, M(e) || "Unknown", l));
    return P({}, t, r);
  }
  function tl(e) {
    return e = (e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext || Xn, rt = Be.current, ae(Be, e), ae(Ge, Ge.current), !0;
  }
  function mu(e, n, t) {
    var r = e.stateNode;
    if (!r) throw Error(c(169));
    t ? (e = hu(e, n, rt), r.__reactInternalMemoizedMergedChildContext = e, de(Ge), de(Be), ae(Be, e)) : de(Ge), ae(Ge, t);
  }
  var Pn = null, rl = !1, Ui = !1;
  function vu(e) {
    Pn === null ? Pn = [e] : Pn.push(e);
  }
  function Od(e) {
    rl = !0, vu(e);
  }
  function Zn() {
    if (!Ui && Pn !== null) {
      Ui = !0;
      var e = 0, n = ie;
      try {
        var t = Pn;
        for (ie = 1; e < t.length; e++) {
          var r = t[e];
          do
            r = r(!0);
          while (r !== null);
        }
        Pn = null, rl = !1;
      } catch (l) {
        throw Pn !== null && (Pn = Pn.slice(e + 1)), ys(si, Zn), l;
      } finally {
        ie = n, Ui = !1;
      }
    }
    return null;
  }
  var Rt = [], zt = 0, ll = null, il = 0, un = [], an = 0, lt = null, Tn = 1, Ln = "";
  function it(e, n) {
    Rt[zt++] = il, Rt[zt++] = ll, ll = e, il = n;
  }
  function gu(e, n, t) {
    un[an++] = Tn, un[an++] = Ln, un[an++] = lt, lt = e;
    var r = Tn;
    e = Ln;
    var l = 32 - hn(r) - 1;
    r &= ~(1 << l), t += 1;
    var i = 32 - hn(n) + l;
    if (30 < i) {
      var s = l - l % 5;
      i = (r & (1 << s) - 1).toString(32), r >>= s, l -= s, Tn = 1 << 32 - hn(n) + l | t << l | r, Ln = i + e;
    } else Tn = 1 << i | t << l | r, Ln = e;
  }
  function qi(e) {
    e.return !== null && (it(e, 1), gu(e, 1, 0));
  }
  function Ai(e) {
    for (; e === ll; ) ll = Rt[--zt], Rt[zt] = null, il = Rt[--zt], Rt[zt] = null;
    for (; e === lt; ) lt = un[--an], un[an] = null, Ln = un[--an], un[an] = null, Tn = un[--an], un[an] = null;
  }
  var ln = null, on = null, he = !1, vn = null;
  function yu(e, n) {
    var t = pn(5, null, null, 0);
    t.elementType = "DELETED", t.stateNode = n, t.return = e, n = e.deletions, n === null ? (e.deletions = [t], e.flags |= 16) : n.push(t);
  }
  function xu(e, n) {
    switch (e.tag) {
      case 5:
        var t = e.type;
        return n = n.nodeType !== 1 || t.toLowerCase() !== n.nodeName.toLowerCase() ? null : n, n !== null ? (e.stateNode = n, ln = e, on = Hn(n.firstChild), !0) : !1;
      case 6:
        return n = e.pendingProps === "" || n.nodeType !== 3 ? null : n, n !== null ? (e.stateNode = n, ln = e, on = null, !0) : !1;
      case 13:
        return n = n.nodeType !== 8 ? null : n, n !== null ? (t = lt !== null ? { id: Tn, overflow: Ln } : null, e.memoizedState = { dehydrated: n, treeContext: t, retryLane: 1073741824 }, t = pn(18, null, null, 0), t.stateNode = n, t.return = e, e.child = t, ln = e, on = null, !0) : !1;
      default:
        return !1;
    }
  }
  function Hi(e) {
    return (e.mode & 1) !== 0 && (e.flags & 128) === 0;
  }
  function Bi(e) {
    if (he) {
      var n = on;
      if (n) {
        var t = n;
        if (!xu(e, n)) {
          if (Hi(e)) throw Error(c(418));
          n = Hn(t.nextSibling);
          var r = ln;
          n && xu(e, n) ? yu(r, t) : (e.flags = e.flags & -4097 | 2, he = !1, ln = e);
        }
      } else {
        if (Hi(e)) throw Error(c(418));
        e.flags = e.flags & -4097 | 2, he = !1, ln = e;
      }
    }
  }
  function wu(e) {
    for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13; ) e = e.return;
    ln = e;
  }
  function ol(e) {
    if (e !== ln) return !1;
    if (!he) return wu(e), he = !0, !1;
    var n;
    if ((n = e.tag !== 3) && !(n = e.tag !== 5) && (n = e.type, n = n !== "head" && n !== "body" && !Mi(e.type, e.memoizedProps)), n && (n = on)) {
      if (Hi(e)) throw ku(), Error(c(418));
      for (; n; ) yu(e, n), n = Hn(n.nextSibling);
    }
    if (wu(e), e.tag === 13) {
      if (e = e.memoizedState, e = e !== null ? e.dehydrated : null, !e) throw Error(c(317));
      e: {
        for (e = e.nextSibling, n = 0; e; ) {
          if (e.nodeType === 8) {
            var t = e.data;
            if (t === "/$") {
              if (n === 0) {
                on = Hn(e.nextSibling);
                break e;
              }
              n--;
            } else t !== "$" && t !== "$!" && t !== "$?" || n++;
          }
          e = e.nextSibling;
        }
        on = null;
      }
    } else on = ln ? Hn(e.stateNode.nextSibling) : null;
    return !0;
  }
  function ku() {
    for (var e = on; e; ) e = Hn(e.nextSibling);
  }
  function Pt() {
    on = ln = null, he = !1;
  }
  function Xi(e) {
    vn === null ? vn = [e] : vn.push(e);
  }
  var Fd = ve.ReactCurrentBatchConfig;
  function cr(e, n, t) {
    if (e = t.ref, e !== null && typeof e != "function" && typeof e != "object") {
      if (t._owner) {
        if (t = t._owner, t) {
          if (t.tag !== 1) throw Error(c(309));
          var r = t.stateNode;
        }
        if (!r) throw Error(c(147, e));
        var l = r, i = "" + e;
        return n !== null && n.ref !== null && typeof n.ref == "function" && n.ref._stringRef === i ? n.ref : (n = function(s) {
          var d = l.refs;
          s === null ? delete d[i] : d[i] = s;
        }, n._stringRef = i, n);
      }
      if (typeof e != "string") throw Error(c(284));
      if (!t._owner) throw Error(c(290, e));
    }
    return e;
  }
  function sl(e, n) {
    throw e = Object.prototype.toString.call(n), Error(c(31, e === "[object Object]" ? "object with keys {" + Object.keys(n).join(", ") + "}" : e));
  }
  function Su(e) {
    var n = e._init;
    return n(e._payload);
  }
  function ju(e) {
    function n(m, p) {
      if (e) {
        var g = m.deletions;
        g === null ? (m.deletions = [p], m.flags |= 16) : g.push(p);
      }
    }
    function t(m, p) {
      if (!e) return null;
      for (; p !== null; ) n(m, p), p = p.sibling;
      return null;
    }
    function r(m, p) {
      for (m = /* @__PURE__ */ new Map(); p !== null; ) p.key !== null ? m.set(p.key, p) : m.set(p.index, p), p = p.sibling;
      return m;
    }
    function l(m, p) {
      return m = $n(m, p), m.index = 0, m.sibling = null, m;
    }
    function i(m, p, g) {
      return m.index = g, e ? (g = m.alternate, g !== null ? (g = g.index, g < p ? (m.flags |= 2, p) : g) : (m.flags |= 2, p)) : (m.flags |= 1048576, p);
    }
    function s(m) {
      return e && m.alternate === null && (m.flags |= 2), m;
    }
    function d(m, p, g, L) {
      return p === null || p.tag !== 6 ? (p = Wo(g, m.mode, L), p.return = m, p) : (p = l(p, g), p.return = m, p);
    }
    function f(m, p, g, L) {
      var V = g.type;
      return V === ge ? N(m, p, g.props.children, L, g.key) : p !== null && (p.elementType === V || typeof V == "object" && V !== null && V.$$typeof === Te && Su(V) === p.type) ? (L = l(p, g.props), L.ref = cr(m, p, g), L.return = m, L) : (L = Ll(g.type, g.key, g.props, null, m.mode, L), L.ref = cr(m, p, g), L.return = m, L);
    }
    function y(m, p, g, L) {
      return p === null || p.tag !== 4 || p.stateNode.containerInfo !== g.containerInfo || p.stateNode.implementation !== g.implementation ? (p = Do(g, m.mode, L), p.return = m, p) : (p = l(p, g.children || []), p.return = m, p);
    }
    function N(m, p, g, L, V) {
      return p === null || p.tag !== 7 ? (p = pt(g, m.mode, L, V), p.return = m, p) : (p = l(p, g), p.return = m, p);
    }
    function C(m, p, g) {
      if (typeof p == "string" && p !== "" || typeof p == "number") return p = Wo("" + p, m.mode, g), p.return = m, p;
      if (typeof p == "object" && p !== null) {
        switch (p.$$typeof) {
          case Re:
            return g = Ll(p.type, p.key, p.props, null, m.mode, g), g.ref = cr(m, null, p), g.return = m, g;
          case Se:
            return p = Do(p, m.mode, g), p.return = m, p;
          case Te:
            var L = p._init;
            return C(m, L(p._payload), g);
        }
        if (Ut(p) || z(p)) return p = pt(p, m.mode, g, null), p.return = m, p;
        sl(m, p);
      }
      return null;
    }
    function j(m, p, g, L) {
      var V = p !== null ? p.key : null;
      if (typeof g == "string" && g !== "" || typeof g == "number") return V !== null ? null : d(m, p, "" + g, L);
      if (typeof g == "object" && g !== null) {
        switch (g.$$typeof) {
          case Re:
            return g.key === V ? f(m, p, g, L) : null;
          case Se:
            return g.key === V ? y(m, p, g, L) : null;
          case Te:
            return V = g._init, j(
              m,
              p,
              V(g._payload),
              L
            );
        }
        if (Ut(g) || z(g)) return V !== null ? null : N(m, p, g, L, null);
        sl(m, g);
      }
      return null;
    }
    function F(m, p, g, L, V) {
      if (typeof L == "string" && L !== "" || typeof L == "number") return m = m.get(g) || null, d(p, m, "" + L, V);
      if (typeof L == "object" && L !== null) {
        switch (L.$$typeof) {
          case Re:
            return m = m.get(L.key === null ? g : L.key) || null, f(p, m, L, V);
          case Se:
            return m = m.get(L.key === null ? g : L.key) || null, y(p, m, L, V);
          case Te:
            var A = L._init;
            return F(m, p, g, A(L._payload), V);
        }
        if (Ut(L) || z(L)) return m = m.get(g) || null, N(p, m, L, V, null);
        sl(p, L);
      }
      return null;
    }
    function W(m, p, g, L) {
      for (var V = null, A = null, H = p, B = p = 0, We = null; H !== null && B < g.length; B++) {
        H.index > B ? (We = H, H = null) : We = H.sibling;
        var re = j(m, H, g[B], L);
        if (re === null) {
          H === null && (H = We);
          break;
        }
        e && H && re.alternate === null && n(m, H), p = i(re, p, B), A === null ? V = re : A.sibling = re, A = re, H = We;
      }
      if (B === g.length) return t(m, H), he && it(m, B), V;
      if (H === null) {
        for (; B < g.length; B++) H = C(m, g[B], L), H !== null && (p = i(H, p, B), A === null ? V = H : A.sibling = H, A = H);
        return he && it(m, B), V;
      }
      for (H = r(m, H); B < g.length; B++) We = F(H, m, B, g[B], L), We !== null && (e && We.alternate !== null && H.delete(We.key === null ? B : We.key), p = i(We, p, B), A === null ? V = We : A.sibling = We, A = We);
      return e && H.forEach(function(et) {
        return n(m, et);
      }), he && it(m, B), V;
    }
    function D(m, p, g, L) {
      var V = z(g);
      if (typeof V != "function") throw Error(c(150));
      if (g = V.call(g), g == null) throw Error(c(151));
      for (var A = V = null, H = p, B = p = 0, We = null, re = g.next(); H !== null && !re.done; B++, re = g.next()) {
        H.index > B ? (We = H, H = null) : We = H.sibling;
        var et = j(m, H, re.value, L);
        if (et === null) {
          H === null && (H = We);
          break;
        }
        e && H && et.alternate === null && n(m, H), p = i(et, p, B), A === null ? V = et : A.sibling = et, A = et, H = We;
      }
      if (re.done) return t(
        m,
        H
      ), he && it(m, B), V;
      if (H === null) {
        for (; !re.done; B++, re = g.next()) re = C(m, re.value, L), re !== null && (p = i(re, p, B), A === null ? V = re : A.sibling = re, A = re);
        return he && it(m, B), V;
      }
      for (H = r(m, H); !re.done; B++, re = g.next()) re = F(H, m, B, re.value, L), re !== null && (e && re.alternate !== null && H.delete(re.key === null ? B : re.key), p = i(re, p, B), A === null ? V = re : A.sibling = re, A = re);
      return e && H.forEach(function(pf) {
        return n(m, pf);
      }), he && it(m, B), V;
    }
    function Ne(m, p, g, L) {
      if (typeof g == "object" && g !== null && g.type === ge && g.key === null && (g = g.props.children), typeof g == "object" && g !== null) {
        switch (g.$$typeof) {
          case Re:
            e: {
              for (var V = g.key, A = p; A !== null; ) {
                if (A.key === V) {
                  if (V = g.type, V === ge) {
                    if (A.tag === 7) {
                      t(m, A.sibling), p = l(A, g.props.children), p.return = m, m = p;
                      break e;
                    }
                  } else if (A.elementType === V || typeof V == "object" && V !== null && V.$$typeof === Te && Su(V) === A.type) {
                    t(m, A.sibling), p = l(A, g.props), p.ref = cr(m, A, g), p.return = m, m = p;
                    break e;
                  }
                  t(m, A);
                  break;
                } else n(m, A);
                A = A.sibling;
              }
              g.type === ge ? (p = pt(g.props.children, m.mode, L, g.key), p.return = m, m = p) : (L = Ll(g.type, g.key, g.props, null, m.mode, L), L.ref = cr(m, p, g), L.return = m, m = L);
            }
            return s(m);
          case Se:
            e: {
              for (A = g.key; p !== null; ) {
                if (p.key === A) if (p.tag === 4 && p.stateNode.containerInfo === g.containerInfo && p.stateNode.implementation === g.implementation) {
                  t(m, p.sibling), p = l(p, g.children || []), p.return = m, m = p;
                  break e;
                } else {
                  t(m, p);
                  break;
                }
                else n(m, p);
                p = p.sibling;
              }
              p = Do(g, m.mode, L), p.return = m, m = p;
            }
            return s(m);
          case Te:
            return A = g._init, Ne(m, p, A(g._payload), L);
        }
        if (Ut(g)) return W(m, p, g, L);
        if (z(g)) return D(m, p, g, L);
        sl(m, g);
      }
      return typeof g == "string" && g !== "" || typeof g == "number" ? (g = "" + g, p !== null && p.tag === 6 ? (t(m, p.sibling), p = l(p, g), p.return = m, m = p) : (t(m, p), p = Wo(g, m.mode, L), p.return = m, m = p), s(m)) : t(m, p);
    }
    return Ne;
  }
  var Tt = ju(!0), Nu = ju(!1), ul = Bn(null), al = null, Lt = null, Zi = null;
  function Ji() {
    Zi = Lt = al = null;
  }
  function Ki(e) {
    var n = ul.current;
    de(ul), e._currentValue = n;
  }
  function Qi(e, n, t) {
    for (; e !== null; ) {
      var r = e.alternate;
      if ((e.childLanes & n) !== n ? (e.childLanes |= n, r !== null && (r.childLanes |= n)) : r !== null && (r.childLanes & n) !== n && (r.childLanes |= n), e === t) break;
      e = e.return;
    }
  }
  function Ot(e, n) {
    al = e, Zi = Lt = null, e = e.dependencies, e !== null && e.firstContext !== null && ((e.lanes & n) !== 0 && (be = !0), e.firstContext = null);
  }
  function cn(e) {
    var n = e._currentValue;
    if (Zi !== e) if (e = { context: e, memoizedValue: n, next: null }, Lt === null) {
      if (al === null) throw Error(c(308));
      Lt = e, al.dependencies = { lanes: 0, firstContext: e };
    } else Lt = Lt.next = e;
    return n;
  }
  var ot = null;
  function Gi(e) {
    ot === null ? ot = [e] : ot.push(e);
  }
  function Cu(e, n, t, r) {
    var l = n.interleaved;
    return l === null ? (t.next = t, Gi(n)) : (t.next = l.next, l.next = t), n.interleaved = t, On(e, r);
  }
  function On(e, n) {
    e.lanes |= n;
    var t = e.alternate;
    for (t !== null && (t.lanes |= n), t = e, e = e.return; e !== null; ) e.childLanes |= n, t = e.alternate, t !== null && (t.childLanes |= n), t = e, e = e.return;
    return t.tag === 3 ? t.stateNode : null;
  }
  var Jn = !1;
  function Yi(e) {
    e.updateQueue = { baseState: e.memoizedState, firstBaseUpdate: null, lastBaseUpdate: null, shared: { pending: null, interleaved: null, lanes: 0 }, effects: null };
  }
  function Eu(e, n) {
    e = e.updateQueue, n.updateQueue === e && (n.updateQueue = { baseState: e.baseState, firstBaseUpdate: e.firstBaseUpdate, lastBaseUpdate: e.lastBaseUpdate, shared: e.shared, effects: e.effects });
  }
  function Fn(e, n) {
    return { eventTime: e, lane: n, tag: 0, payload: null, callback: null, next: null };
  }
  function Kn(e, n, t) {
    var r = e.updateQueue;
    if (r === null) return null;
    if (r = r.shared, (te & 2) !== 0) {
      var l = r.pending;
      return l === null ? n.next = n : (n.next = l.next, l.next = n), r.pending = n, On(e, t);
    }
    return l = r.interleaved, l === null ? (n.next = n, Gi(r)) : (n.next = l.next, l.next = n), r.interleaved = n, On(e, t);
  }
  function cl(e, n, t) {
    if (n = n.updateQueue, n !== null && (n = n.shared, (t & 4194240) !== 0)) {
      var r = n.lanes;
      r &= e.pendingLanes, t |= r, n.lanes = t, ci(e, t);
    }
  }
  function Ru(e, n) {
    var t = e.updateQueue, r = e.alternate;
    if (r !== null && (r = r.updateQueue, t === r)) {
      var l = null, i = null;
      if (t = t.firstBaseUpdate, t !== null) {
        do {
          var s = { eventTime: t.eventTime, lane: t.lane, tag: t.tag, payload: t.payload, callback: t.callback, next: null };
          i === null ? l = i = s : i = i.next = s, t = t.next;
        } while (t !== null);
        i === null ? l = i = n : i = i.next = n;
      } else l = i = n;
      t = { baseState: r.baseState, firstBaseUpdate: l, lastBaseUpdate: i, shared: r.shared, effects: r.effects }, e.updateQueue = t;
      return;
    }
    e = t.lastBaseUpdate, e === null ? t.firstBaseUpdate = n : e.next = n, t.lastBaseUpdate = n;
  }
  function dl(e, n, t, r) {
    var l = e.updateQueue;
    Jn = !1;
    var i = l.firstBaseUpdate, s = l.lastBaseUpdate, d = l.shared.pending;
    if (d !== null) {
      l.shared.pending = null;
      var f = d, y = f.next;
      f.next = null, s === null ? i = y : s.next = y, s = f;
      var N = e.alternate;
      N !== null && (N = N.updateQueue, d = N.lastBaseUpdate, d !== s && (d === null ? N.firstBaseUpdate = y : d.next = y, N.lastBaseUpdate = f));
    }
    if (i !== null) {
      var C = l.baseState;
      s = 0, N = y = f = null, d = i;
      do {
        var j = d.lane, F = d.eventTime;
        if ((r & j) === j) {
          N !== null && (N = N.next = {
            eventTime: F,
            lane: 0,
            tag: d.tag,
            payload: d.payload,
            callback: d.callback,
            next: null
          });
          e: {
            var W = e, D = d;
            switch (j = n, F = t, D.tag) {
              case 1:
                if (W = D.payload, typeof W == "function") {
                  C = W.call(F, C, j);
                  break e;
                }
                C = W;
                break e;
              case 3:
                W.flags = W.flags & -65537 | 128;
              case 0:
                if (W = D.payload, j = typeof W == "function" ? W.call(F, C, j) : W, j == null) break e;
                C = P({}, C, j);
                break e;
              case 2:
                Jn = !0;
            }
          }
          d.callback !== null && d.lane !== 0 && (e.flags |= 64, j = l.effects, j === null ? l.effects = [d] : j.push(d));
        } else F = { eventTime: F, lane: j, tag: d.tag, payload: d.payload, callback: d.callback, next: null }, N === null ? (y = N = F, f = C) : N = N.next = F, s |= j;
        if (d = d.next, d === null) {
          if (d = l.shared.pending, d === null) break;
          j = d, d = j.next, j.next = null, l.lastBaseUpdate = j, l.shared.pending = null;
        }
      } while (!0);
      if (N === null && (f = C), l.baseState = f, l.firstBaseUpdate = y, l.lastBaseUpdate = N, n = l.shared.interleaved, n !== null) {
        l = n;
        do
          s |= l.lane, l = l.next;
        while (l !== n);
      } else i === null && (l.shared.lanes = 0);
      at |= s, e.lanes = s, e.memoizedState = C;
    }
  }
  function zu(e, n, t) {
    if (e = n.effects, n.effects = null, e !== null) for (n = 0; n < e.length; n++) {
      var r = e[n], l = r.callback;
      if (l !== null) {
        if (r.callback = null, r = t, typeof l != "function") throw Error(c(191, l));
        l.call(r);
      }
    }
  }
  var dr = {}, Nn = Bn(dr), fr = Bn(dr), pr = Bn(dr);
  function st(e) {
    if (e === dr) throw Error(c(174));
    return e;
  }
  function bi(e, n) {
    switch (ae(pr, n), ae(fr, e), ae(Nn, dr), e = n.nodeType, e) {
      case 9:
      case 11:
        n = (n = n.documentElement) ? n.namespaceURI : _l(null, "");
        break;
      default:
        e = e === 8 ? n.parentNode : n, n = e.namespaceURI || null, e = e.tagName, n = _l(n, e);
    }
    de(Nn), ae(Nn, n);
  }
  function Ft() {
    de(Nn), de(fr), de(pr);
  }
  function Pu(e) {
    st(pr.current);
    var n = st(Nn.current), t = _l(n, e.type);
    n !== t && (ae(fr, e), ae(Nn, t));
  }
  function _i(e) {
    fr.current === e && (de(Nn), de(fr));
  }
  var ye = Bn(0);
  function fl(e) {
    for (var n = e; n !== null; ) {
      if (n.tag === 13) {
        var t = n.memoizedState;
        if (t !== null && (t = t.dehydrated, t === null || t.data === "$?" || t.data === "$!")) return n;
      } else if (n.tag === 19 && n.memoizedProps.revealOrder !== void 0) {
        if ((n.flags & 128) !== 0) return n;
      } else if (n.child !== null) {
        n.child.return = n, n = n.child;
        continue;
      }
      if (n === e) break;
      for (; n.sibling === null; ) {
        if (n.return === null || n.return === e) return null;
        n = n.return;
      }
      n.sibling.return = n.return, n = n.sibling;
    }
    return null;
  }
  var $i = [];
  function eo() {
    for (var e = 0; e < $i.length; e++) $i[e]._workInProgressVersionPrimary = null;
    $i.length = 0;
  }
  var pl = ve.ReactCurrentDispatcher, no = ve.ReactCurrentBatchConfig, ut = 0, xe = null, Le = null, Me = null, hl = !1, hr = !1, mr = 0, Md = 0;
  function Xe() {
    throw Error(c(321));
  }
  function to(e, n) {
    if (n === null) return !1;
    for (var t = 0; t < n.length && t < e.length; t++) if (!mn(e[t], n[t])) return !1;
    return !0;
  }
  function ro(e, n, t, r, l, i) {
    if (ut = i, xe = n, n.memoizedState = null, n.updateQueue = null, n.lanes = 0, pl.current = e === null || e.memoizedState === null ? Vd : Ud, e = t(r, l), hr) {
      i = 0;
      do {
        if (hr = !1, mr = 0, 25 <= i) throw Error(c(301));
        i += 1, Me = Le = null, n.updateQueue = null, pl.current = qd, e = t(r, l);
      } while (hr);
    }
    if (pl.current = gl, n = Le !== null && Le.next !== null, ut = 0, Me = Le = xe = null, hl = !1, n) throw Error(c(300));
    return e;
  }
  function lo() {
    var e = mr !== 0;
    return mr = 0, e;
  }
  function Cn() {
    var e = { memoizedState: null, baseState: null, baseQueue: null, queue: null, next: null };
    return Me === null ? xe.memoizedState = Me = e : Me = Me.next = e, Me;
  }
  function dn() {
    if (Le === null) {
      var e = xe.alternate;
      e = e !== null ? e.memoizedState : null;
    } else e = Le.next;
    var n = Me === null ? xe.memoizedState : Me.next;
    if (n !== null) Me = n, Le = e;
    else {
      if (e === null) throw Error(c(310));
      Le = e, e = { memoizedState: Le.memoizedState, baseState: Le.baseState, baseQueue: Le.baseQueue, queue: Le.queue, next: null }, Me === null ? xe.memoizedState = Me = e : Me = Me.next = e;
    }
    return Me;
  }
  function vr(e, n) {
    return typeof n == "function" ? n(e) : n;
  }
  function io(e) {
    var n = dn(), t = n.queue;
    if (t === null) throw Error(c(311));
    t.lastRenderedReducer = e;
    var r = Le, l = r.baseQueue, i = t.pending;
    if (i !== null) {
      if (l !== null) {
        var s = l.next;
        l.next = i.next, i.next = s;
      }
      r.baseQueue = l = i, t.pending = null;
    }
    if (l !== null) {
      i = l.next, r = r.baseState;
      var d = s = null, f = null, y = i;
      do {
        var N = y.lane;
        if ((ut & N) === N) f !== null && (f = f.next = { lane: 0, action: y.action, hasEagerState: y.hasEagerState, eagerState: y.eagerState, next: null }), r = y.hasEagerState ? y.eagerState : e(r, y.action);
        else {
          var C = {
            lane: N,
            action: y.action,
            hasEagerState: y.hasEagerState,
            eagerState: y.eagerState,
            next: null
          };
          f === null ? (d = f = C, s = r) : f = f.next = C, xe.lanes |= N, at |= N;
        }
        y = y.next;
      } while (y !== null && y !== i);
      f === null ? s = r : f.next = d, mn(r, n.memoizedState) || (be = !0), n.memoizedState = r, n.baseState = s, n.baseQueue = f, t.lastRenderedState = r;
    }
    if (e = t.interleaved, e !== null) {
      l = e;
      do
        i = l.lane, xe.lanes |= i, at |= i, l = l.next;
      while (l !== e);
    } else l === null && (t.lanes = 0);
    return [n.memoizedState, t.dispatch];
  }
  function oo(e) {
    var n = dn(), t = n.queue;
    if (t === null) throw Error(c(311));
    t.lastRenderedReducer = e;
    var r = t.dispatch, l = t.pending, i = n.memoizedState;
    if (l !== null) {
      t.pending = null;
      var s = l = l.next;
      do
        i = e(i, s.action), s = s.next;
      while (s !== l);
      mn(i, n.memoizedState) || (be = !0), n.memoizedState = i, n.baseQueue === null && (n.baseState = i), t.lastRenderedState = i;
    }
    return [i, r];
  }
  function Tu() {
  }
  function Lu(e, n) {
    var t = xe, r = dn(), l = n(), i = !mn(r.memoizedState, l);
    if (i && (r.memoizedState = l, be = !0), r = r.queue, so(Mu.bind(null, t, r, e), [e]), r.getSnapshot !== n || i || Me !== null && Me.memoizedState.tag & 1) {
      if (t.flags |= 2048, gr(9, Fu.bind(null, t, r, l, n), void 0, null), Ie === null) throw Error(c(349));
      (ut & 30) !== 0 || Ou(t, n, l);
    }
    return l;
  }
  function Ou(e, n, t) {
    e.flags |= 16384, e = { getSnapshot: n, value: t }, n = xe.updateQueue, n === null ? (n = { lastEffect: null, stores: null }, xe.updateQueue = n, n.stores = [e]) : (t = n.stores, t === null ? n.stores = [e] : t.push(e));
  }
  function Fu(e, n, t, r) {
    n.value = t, n.getSnapshot = r, Iu(n) && Wu(e);
  }
  function Mu(e, n, t) {
    return t(function() {
      Iu(n) && Wu(e);
    });
  }
  function Iu(e) {
    var n = e.getSnapshot;
    e = e.value;
    try {
      var t = n();
      return !mn(e, t);
    } catch {
      return !0;
    }
  }
  function Wu(e) {
    var n = On(e, 1);
    n !== null && wn(n, e, 1, -1);
  }
  function Du(e) {
    var n = Cn();
    return typeof e == "function" && (e = e()), n.memoizedState = n.baseState = e, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: vr, lastRenderedState: e }, n.queue = e, e = e.dispatch = Dd.bind(null, xe, e), [n.memoizedState, e];
  }
  function gr(e, n, t, r) {
    return e = { tag: e, create: n, destroy: t, deps: r, next: null }, n = xe.updateQueue, n === null ? (n = { lastEffect: null, stores: null }, xe.updateQueue = n, n.lastEffect = e.next = e) : (t = n.lastEffect, t === null ? n.lastEffect = e.next = e : (r = t.next, t.next = e, e.next = r, n.lastEffect = e)), e;
  }
  function Vu() {
    return dn().memoizedState;
  }
  function ml(e, n, t, r) {
    var l = Cn();
    xe.flags |= e, l.memoizedState = gr(1 | n, t, void 0, r === void 0 ? null : r);
  }
  function vl(e, n, t, r) {
    var l = dn();
    r = r === void 0 ? null : r;
    var i = void 0;
    if (Le !== null) {
      var s = Le.memoizedState;
      if (i = s.destroy, r !== null && to(r, s.deps)) {
        l.memoizedState = gr(n, t, i, r);
        return;
      }
    }
    xe.flags |= e, l.memoizedState = gr(1 | n, t, i, r);
  }
  function Uu(e, n) {
    return ml(8390656, 8, e, n);
  }
  function so(e, n) {
    return vl(2048, 8, e, n);
  }
  function qu(e, n) {
    return vl(4, 2, e, n);
  }
  function Au(e, n) {
    return vl(4, 4, e, n);
  }
  function Hu(e, n) {
    if (typeof n == "function") return e = e(), n(e), function() {
      n(null);
    };
    if (n != null) return e = e(), n.current = e, function() {
      n.current = null;
    };
  }
  function Bu(e, n, t) {
    return t = t != null ? t.concat([e]) : null, vl(4, 4, Hu.bind(null, n, e), t);
  }
  function uo() {
  }
  function Xu(e, n) {
    var t = dn();
    n = n === void 0 ? null : n;
    var r = t.memoizedState;
    return r !== null && n !== null && to(n, r[1]) ? r[0] : (t.memoizedState = [e, n], e);
  }
  function Zu(e, n) {
    var t = dn();
    n = n === void 0 ? null : n;
    var r = t.memoizedState;
    return r !== null && n !== null && to(n, r[1]) ? r[0] : (e = e(), t.memoizedState = [e, n], e);
  }
  function Ju(e, n, t) {
    return (ut & 21) === 0 ? (e.baseState && (e.baseState = !1, be = !0), e.memoizedState = t) : (mn(t, n) || (t = Ss(), xe.lanes |= t, at |= t, e.baseState = !0), n);
  }
  function Id(e, n) {
    var t = ie;
    ie = t !== 0 && 4 > t ? t : 4, e(!0);
    var r = no.transition;
    no.transition = {};
    try {
      e(!1), n();
    } finally {
      ie = t, no.transition = r;
    }
  }
  function Ku() {
    return dn().memoizedState;
  }
  function Wd(e, n, t) {
    var r = bn(e);
    if (t = { lane: r, action: t, hasEagerState: !1, eagerState: null, next: null }, Qu(e)) Gu(n, t);
    else if (t = Cu(e, n, t, r), t !== null) {
      var l = Qe();
      wn(t, e, r, l), Yu(t, n, r);
    }
  }
  function Dd(e, n, t) {
    var r = bn(e), l = { lane: r, action: t, hasEagerState: !1, eagerState: null, next: null };
    if (Qu(e)) Gu(n, l);
    else {
      var i = e.alternate;
      if (e.lanes === 0 && (i === null || i.lanes === 0) && (i = n.lastRenderedReducer, i !== null)) try {
        var s = n.lastRenderedState, d = i(s, t);
        if (l.hasEagerState = !0, l.eagerState = d, mn(d, s)) {
          var f = n.interleaved;
          f === null ? (l.next = l, Gi(n)) : (l.next = f.next, f.next = l), n.interleaved = l;
          return;
        }
      } catch {
      } finally {
      }
      t = Cu(e, n, l, r), t !== null && (l = Qe(), wn(t, e, r, l), Yu(t, n, r));
    }
  }
  function Qu(e) {
    var n = e.alternate;
    return e === xe || n !== null && n === xe;
  }
  function Gu(e, n) {
    hr = hl = !0;
    var t = e.pending;
    t === null ? n.next = n : (n.next = t.next, t.next = n), e.pending = n;
  }
  function Yu(e, n, t) {
    if ((t & 4194240) !== 0) {
      var r = n.lanes;
      r &= e.pendingLanes, t |= r, n.lanes = t, ci(e, t);
    }
  }
  var gl = { readContext: cn, useCallback: Xe, useContext: Xe, useEffect: Xe, useImperativeHandle: Xe, useInsertionEffect: Xe, useLayoutEffect: Xe, useMemo: Xe, useReducer: Xe, useRef: Xe, useState: Xe, useDebugValue: Xe, useDeferredValue: Xe, useTransition: Xe, useMutableSource: Xe, useSyncExternalStore: Xe, useId: Xe, unstable_isNewReconciler: !1 }, Vd = { readContext: cn, useCallback: function(e, n) {
    return Cn().memoizedState = [e, n === void 0 ? null : n], e;
  }, useContext: cn, useEffect: Uu, useImperativeHandle: function(e, n, t) {
    return t = t != null ? t.concat([e]) : null, ml(
      4194308,
      4,
      Hu.bind(null, n, e),
      t
    );
  }, useLayoutEffect: function(e, n) {
    return ml(4194308, 4, e, n);
  }, useInsertionEffect: function(e, n) {
    return ml(4, 2, e, n);
  }, useMemo: function(e, n) {
    var t = Cn();
    return n = n === void 0 ? null : n, e = e(), t.memoizedState = [e, n], e;
  }, useReducer: function(e, n, t) {
    var r = Cn();
    return n = t !== void 0 ? t(n) : n, r.memoizedState = r.baseState = n, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: e, lastRenderedState: n }, r.queue = e, e = e.dispatch = Wd.bind(null, xe, e), [r.memoizedState, e];
  }, useRef: function(e) {
    var n = Cn();
    return e = { current: e }, n.memoizedState = e;
  }, useState: Du, useDebugValue: uo, useDeferredValue: function(e) {
    return Cn().memoizedState = e;
  }, useTransition: function() {
    var e = Du(!1), n = e[0];
    return e = Id.bind(null, e[1]), Cn().memoizedState = e, [n, e];
  }, useMutableSource: function() {
  }, useSyncExternalStore: function(e, n, t) {
    var r = xe, l = Cn();
    if (he) {
      if (t === void 0) throw Error(c(407));
      t = t();
    } else {
      if (t = n(), Ie === null) throw Error(c(349));
      (ut & 30) !== 0 || Ou(r, n, t);
    }
    l.memoizedState = t;
    var i = { value: t, getSnapshot: n };
    return l.queue = i, Uu(Mu.bind(
      null,
      r,
      i,
      e
    ), [e]), r.flags |= 2048, gr(9, Fu.bind(null, r, i, t, n), void 0, null), t;
  }, useId: function() {
    var e = Cn(), n = Ie.identifierPrefix;
    if (he) {
      var t = Ln, r = Tn;
      t = (r & ~(1 << 32 - hn(r) - 1)).toString(32) + t, n = ":" + n + "R" + t, t = mr++, 0 < t && (n += "H" + t.toString(32)), n += ":";
    } else t = Md++, n = ":" + n + "r" + t.toString(32) + ":";
    return e.memoizedState = n;
  }, unstable_isNewReconciler: !1 }, Ud = {
    readContext: cn,
    useCallback: Xu,
    useContext: cn,
    useEffect: so,
    useImperativeHandle: Bu,
    useInsertionEffect: qu,
    useLayoutEffect: Au,
    useMemo: Zu,
    useReducer: io,
    useRef: Vu,
    useState: function() {
      return io(vr);
    },
    useDebugValue: uo,
    useDeferredValue: function(e) {
      var n = dn();
      return Ju(n, Le.memoizedState, e);
    },
    useTransition: function() {
      var e = io(vr)[0], n = dn().memoizedState;
      return [e, n];
    },
    useMutableSource: Tu,
    useSyncExternalStore: Lu,
    useId: Ku,
    unstable_isNewReconciler: !1
  }, qd = { readContext: cn, useCallback: Xu, useContext: cn, useEffect: so, useImperativeHandle: Bu, useInsertionEffect: qu, useLayoutEffect: Au, useMemo: Zu, useReducer: oo, useRef: Vu, useState: function() {
    return oo(vr);
  }, useDebugValue: uo, useDeferredValue: function(e) {
    var n = dn();
    return Le === null ? n.memoizedState = e : Ju(n, Le.memoizedState, e);
  }, useTransition: function() {
    var e = oo(vr)[0], n = dn().memoizedState;
    return [e, n];
  }, useMutableSource: Tu, useSyncExternalStore: Lu, useId: Ku, unstable_isNewReconciler: !1 };
  function gn(e, n) {
    if (e && e.defaultProps) {
      n = P({}, n), e = e.defaultProps;
      for (var t in e) n[t] === void 0 && (n[t] = e[t]);
      return n;
    }
    return n;
  }
  function ao(e, n, t, r) {
    n = e.memoizedState, t = t(r, n), t = t == null ? n : P({}, n, t), e.memoizedState = t, e.lanes === 0 && (e.updateQueue.baseState = t);
  }
  var yl = { isMounted: function(e) {
    return (e = e._reactInternals) ? nt(e) === e : !1;
  }, enqueueSetState: function(e, n, t) {
    e = e._reactInternals;
    var r = Qe(), l = bn(e), i = Fn(r, l);
    i.payload = n, t != null && (i.callback = t), n = Kn(e, i, l), n !== null && (wn(n, e, l, r), cl(n, e, l));
  }, enqueueReplaceState: function(e, n, t) {
    e = e._reactInternals;
    var r = Qe(), l = bn(e), i = Fn(r, l);
    i.tag = 1, i.payload = n, t != null && (i.callback = t), n = Kn(e, i, l), n !== null && (wn(n, e, l, r), cl(n, e, l));
  }, enqueueForceUpdate: function(e, n) {
    e = e._reactInternals;
    var t = Qe(), r = bn(e), l = Fn(t, r);
    l.tag = 2, n != null && (l.callback = n), n = Kn(e, l, r), n !== null && (wn(n, e, r, t), cl(n, e, r));
  } };
  function bu(e, n, t, r, l, i, s) {
    return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, i, s) : n.prototype && n.prototype.isPureReactComponent ? !rr(t, r) || !rr(l, i) : !0;
  }
  function _u(e, n, t) {
    var r = !1, l = Xn, i = n.contextType;
    return typeof i == "object" && i !== null ? i = cn(i) : (l = Ye(n) ? rt : Be.current, r = n.contextTypes, i = (r = r != null) ? Et(e, l) : Xn), n = new n(t, i), e.memoizedState = n.state !== null && n.state !== void 0 ? n.state : null, n.updater = yl, e.stateNode = n, n._reactInternals = e, r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = l, e.__reactInternalMemoizedMaskedChildContext = i), n;
  }
  function $u(e, n, t, r) {
    e = n.state, typeof n.componentWillReceiveProps == "function" && n.componentWillReceiveProps(t, r), typeof n.UNSAFE_componentWillReceiveProps == "function" && n.UNSAFE_componentWillReceiveProps(t, r), n.state !== e && yl.enqueueReplaceState(n, n.state, null);
  }
  function co(e, n, t, r) {
    var l = e.stateNode;
    l.props = t, l.state = e.memoizedState, l.refs = {}, Yi(e);
    var i = n.contextType;
    typeof i == "object" && i !== null ? l.context = cn(i) : (i = Ye(n) ? rt : Be.current, l.context = Et(e, i)), l.state = e.memoizedState, i = n.getDerivedStateFromProps, typeof i == "function" && (ao(e, n, i, t), l.state = e.memoizedState), typeof n.getDerivedStateFromProps == "function" || typeof l.getSnapshotBeforeUpdate == "function" || typeof l.UNSAFE_componentWillMount != "function" && typeof l.componentWillMount != "function" || (n = l.state, typeof l.componentWillMount == "function" && l.componentWillMount(), typeof l.UNSAFE_componentWillMount == "function" && l.UNSAFE_componentWillMount(), n !== l.state && yl.enqueueReplaceState(l, l.state, null), dl(e, t, l, r), l.state = e.memoizedState), typeof l.componentDidMount == "function" && (e.flags |= 4194308);
  }
  function Mt(e, n) {
    try {
      var t = "", r = n;
      do
        t += _(r), r = r.return;
      while (r);
      var l = t;
    } catch (i) {
      l = `
Error generating stack: ` + i.message + `
` + i.stack;
    }
    return { value: e, source: n, stack: l, digest: null };
  }
  function fo(e, n, t) {
    return { value: e, source: null, stack: t ?? null, digest: n ?? null };
  }
  function po(e, n) {
    try {
      console.error(n.value);
    } catch (t) {
      setTimeout(function() {
        throw t;
      });
    }
  }
  var Ad = typeof WeakMap == "function" ? WeakMap : Map;
  function ea(e, n, t) {
    t = Fn(-1, t), t.tag = 3, t.payload = { element: null };
    var r = n.value;
    return t.callback = function() {
      Cl || (Cl = !0, zo = r), po(e, n);
    }, t;
  }
  function na(e, n, t) {
    t = Fn(-1, t), t.tag = 3;
    var r = e.type.getDerivedStateFromError;
    if (typeof r == "function") {
      var l = n.value;
      t.payload = function() {
        return r(l);
      }, t.callback = function() {
        po(e, n);
      };
    }
    var i = e.stateNode;
    return i !== null && typeof i.componentDidCatch == "function" && (t.callback = function() {
      po(e, n), typeof r != "function" && (Gn === null ? Gn = /* @__PURE__ */ new Set([this]) : Gn.add(this));
      var s = n.stack;
      this.componentDidCatch(n.value, { componentStack: s !== null ? s : "" });
    }), t;
  }
  function ta(e, n, t) {
    var r = e.pingCache;
    if (r === null) {
      r = e.pingCache = new Ad();
      var l = /* @__PURE__ */ new Set();
      r.set(n, l);
    } else l = r.get(n), l === void 0 && (l = /* @__PURE__ */ new Set(), r.set(n, l));
    l.has(t) || (l.add(t), e = nf.bind(null, e, n, t), n.then(e, e));
  }
  function ra(e) {
    do {
      var n;
      if ((n = e.tag === 13) && (n = e.memoizedState, n = n !== null ? n.dehydrated !== null : !0), n) return e;
      e = e.return;
    } while (e !== null);
    return null;
  }
  function la(e, n, t, r, l) {
    return (e.mode & 1) === 0 ? (e === n ? e.flags |= 65536 : (e.flags |= 128, t.flags |= 131072, t.flags &= -52805, t.tag === 1 && (t.alternate === null ? t.tag = 17 : (n = Fn(-1, 1), n.tag = 2, Kn(t, n, 1))), t.lanes |= 1), e) : (e.flags |= 65536, e.lanes = l, e);
  }
  var Hd = ve.ReactCurrentOwner, be = !1;
  function Ke(e, n, t, r) {
    n.child = e === null ? Nu(n, null, t, r) : Tt(n, e.child, t, r);
  }
  function ia(e, n, t, r, l) {
    t = t.render;
    var i = n.ref;
    return Ot(n, l), r = ro(e, n, t, r, i, l), t = lo(), e !== null && !be ? (n.updateQueue = e.updateQueue, n.flags &= -2053, e.lanes &= ~l, Mn(e, n, l)) : (he && t && qi(n), n.flags |= 1, Ke(e, n, r, l), n.child);
  }
  function oa(e, n, t, r, l) {
    if (e === null) {
      var i = t.type;
      return typeof i == "function" && !Io(i) && i.defaultProps === void 0 && t.compare === null && t.defaultProps === void 0 ? (n.tag = 15, n.type = i, sa(e, n, i, r, l)) : (e = Ll(t.type, null, r, n, n.mode, l), e.ref = n.ref, e.return = n, n.child = e);
    }
    if (i = e.child, (e.lanes & l) === 0) {
      var s = i.memoizedProps;
      if (t = t.compare, t = t !== null ? t : rr, t(s, r) && e.ref === n.ref) return Mn(e, n, l);
    }
    return n.flags |= 1, e = $n(i, r), e.ref = n.ref, e.return = n, n.child = e;
  }
  function sa(e, n, t, r, l) {
    if (e !== null) {
      var i = e.memoizedProps;
      if (rr(i, r) && e.ref === n.ref) if (be = !1, n.pendingProps = r = i, (e.lanes & l) !== 0) (e.flags & 131072) !== 0 && (be = !0);
      else return n.lanes = e.lanes, Mn(e, n, l);
    }
    return ho(e, n, t, r, l);
  }
  function ua(e, n, t) {
    var r = n.pendingProps, l = r.children, i = e !== null ? e.memoizedState : null;
    if (r.mode === "hidden") if ((n.mode & 1) === 0) n.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, ae(Wt, sn), sn |= t;
    else {
      if ((t & 1073741824) === 0) return e = i !== null ? i.baseLanes | t : t, n.lanes = n.childLanes = 1073741824, n.memoizedState = { baseLanes: e, cachePool: null, transitions: null }, n.updateQueue = null, ae(Wt, sn), sn |= e, null;
      n.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, r = i !== null ? i.baseLanes : t, ae(Wt, sn), sn |= r;
    }
    else i !== null ? (r = i.baseLanes | t, n.memoizedState = null) : r = t, ae(Wt, sn), sn |= r;
    return Ke(e, n, l, t), n.child;
  }
  function aa(e, n) {
    var t = n.ref;
    (e === null && t !== null || e !== null && e.ref !== t) && (n.flags |= 512, n.flags |= 2097152);
  }
  function ho(e, n, t, r, l) {
    var i = Ye(t) ? rt : Be.current;
    return i = Et(n, i), Ot(n, l), t = ro(e, n, t, r, i, l), r = lo(), e !== null && !be ? (n.updateQueue = e.updateQueue, n.flags &= -2053, e.lanes &= ~l, Mn(e, n, l)) : (he && r && qi(n), n.flags |= 1, Ke(e, n, t, l), n.child);
  }
  function ca(e, n, t, r, l) {
    if (Ye(t)) {
      var i = !0;
      tl(n);
    } else i = !1;
    if (Ot(n, l), n.stateNode === null) wl(e, n), _u(n, t, r), co(n, t, r, l), r = !0;
    else if (e === null) {
      var s = n.stateNode, d = n.memoizedProps;
      s.props = d;
      var f = s.context, y = t.contextType;
      typeof y == "object" && y !== null ? y = cn(y) : (y = Ye(t) ? rt : Be.current, y = Et(n, y));
      var N = t.getDerivedStateFromProps, C = typeof N == "function" || typeof s.getSnapshotBeforeUpdate == "function";
      C || typeof s.UNSAFE_componentWillReceiveProps != "function" && typeof s.componentWillReceiveProps != "function" || (d !== r || f !== y) && $u(n, s, r, y), Jn = !1;
      var j = n.memoizedState;
      s.state = j, dl(n, r, s, l), f = n.memoizedState, d !== r || j !== f || Ge.current || Jn ? (typeof N == "function" && (ao(n, t, N, r), f = n.memoizedState), (d = Jn || bu(n, t, d, r, j, f, y)) ? (C || typeof s.UNSAFE_componentWillMount != "function" && typeof s.componentWillMount != "function" || (typeof s.componentWillMount == "function" && s.componentWillMount(), typeof s.UNSAFE_componentWillMount == "function" && s.UNSAFE_componentWillMount()), typeof s.componentDidMount == "function" && (n.flags |= 4194308)) : (typeof s.componentDidMount == "function" && (n.flags |= 4194308), n.memoizedProps = r, n.memoizedState = f), s.props = r, s.state = f, s.context = y, r = d) : (typeof s.componentDidMount == "function" && (n.flags |= 4194308), r = !1);
    } else {
      s = n.stateNode, Eu(e, n), d = n.memoizedProps, y = n.type === n.elementType ? d : gn(n.type, d), s.props = y, C = n.pendingProps, j = s.context, f = t.contextType, typeof f == "object" && f !== null ? f = cn(f) : (f = Ye(t) ? rt : Be.current, f = Et(n, f));
      var F = t.getDerivedStateFromProps;
      (N = typeof F == "function" || typeof s.getSnapshotBeforeUpdate == "function") || typeof s.UNSAFE_componentWillReceiveProps != "function" && typeof s.componentWillReceiveProps != "function" || (d !== C || j !== f) && $u(n, s, r, f), Jn = !1, j = n.memoizedState, s.state = j, dl(n, r, s, l);
      var W = n.memoizedState;
      d !== C || j !== W || Ge.current || Jn ? (typeof F == "function" && (ao(n, t, F, r), W = n.memoizedState), (y = Jn || bu(n, t, y, r, j, W, f) || !1) ? (N || typeof s.UNSAFE_componentWillUpdate != "function" && typeof s.componentWillUpdate != "function" || (typeof s.componentWillUpdate == "function" && s.componentWillUpdate(r, W, f), typeof s.UNSAFE_componentWillUpdate == "function" && s.UNSAFE_componentWillUpdate(r, W, f)), typeof s.componentDidUpdate == "function" && (n.flags |= 4), typeof s.getSnapshotBeforeUpdate == "function" && (n.flags |= 1024)) : (typeof s.componentDidUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 4), typeof s.getSnapshotBeforeUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 1024), n.memoizedProps = r, n.memoizedState = W), s.props = r, s.state = W, s.context = f, r = y) : (typeof s.componentDidUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 4), typeof s.getSnapshotBeforeUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 1024), r = !1);
    }
    return mo(e, n, t, r, i, l);
  }
  function mo(e, n, t, r, l, i) {
    aa(e, n);
    var s = (n.flags & 128) !== 0;
    if (!r && !s) return l && mu(n, t, !1), Mn(e, n, i);
    r = n.stateNode, Hd.current = n;
    var d = s && typeof t.getDerivedStateFromError != "function" ? null : r.render();
    return n.flags |= 1, e !== null && s ? (n.child = Tt(n, e.child, null, i), n.child = Tt(n, null, d, i)) : Ke(e, n, d, i), n.memoizedState = r.state, l && mu(n, t, !0), n.child;
  }
  function da(e) {
    var n = e.stateNode;
    n.pendingContext ? pu(e, n.pendingContext, n.pendingContext !== n.context) : n.context && pu(e, n.context, !1), bi(e, n.containerInfo);
  }
  function fa(e, n, t, r, l) {
    return Pt(), Xi(l), n.flags |= 256, Ke(e, n, t, r), n.child;
  }
  var vo = { dehydrated: null, treeContext: null, retryLane: 0 };
  function go(e) {
    return { baseLanes: e, cachePool: null, transitions: null };
  }
  function pa(e, n, t) {
    var r = n.pendingProps, l = ye.current, i = !1, s = (n.flags & 128) !== 0, d;
    if ((d = s) || (d = e !== null && e.memoizedState === null ? !1 : (l & 2) !== 0), d ? (i = !0, n.flags &= -129) : (e === null || e.memoizedState !== null) && (l |= 1), ae(ye, l & 1), e === null)
      return Bi(n), e = n.memoizedState, e !== null && (e = e.dehydrated, e !== null) ? ((n.mode & 1) === 0 ? n.lanes = 1 : e.data === "$!" ? n.lanes = 8 : n.lanes = 1073741824, null) : (s = r.children, e = r.fallback, i ? (r = n.mode, i = n.child, s = { mode: "hidden", children: s }, (r & 1) === 0 && i !== null ? (i.childLanes = 0, i.pendingProps = s) : i = Ol(s, r, 0, null), e = pt(e, r, t, null), i.return = n, e.return = n, i.sibling = e, n.child = i, n.child.memoizedState = go(t), n.memoizedState = vo, e) : yo(n, s));
    if (l = e.memoizedState, l !== null && (d = l.dehydrated, d !== null)) return Bd(e, n, s, r, d, l, t);
    if (i) {
      i = r.fallback, s = n.mode, l = e.child, d = l.sibling;
      var f = { mode: "hidden", children: r.children };
      return (s & 1) === 0 && n.child !== l ? (r = n.child, r.childLanes = 0, r.pendingProps = f, n.deletions = null) : (r = $n(l, f), r.subtreeFlags = l.subtreeFlags & 14680064), d !== null ? i = $n(d, i) : (i = pt(i, s, t, null), i.flags |= 2), i.return = n, r.return = n, r.sibling = i, n.child = r, r = i, i = n.child, s = e.child.memoizedState, s = s === null ? go(t) : { baseLanes: s.baseLanes | t, cachePool: null, transitions: s.transitions }, i.memoizedState = s, i.childLanes = e.childLanes & ~t, n.memoizedState = vo, r;
    }
    return i = e.child, e = i.sibling, r = $n(i, { mode: "visible", children: r.children }), (n.mode & 1) === 0 && (r.lanes = t), r.return = n, r.sibling = null, e !== null && (t = n.deletions, t === null ? (n.deletions = [e], n.flags |= 16) : t.push(e)), n.child = r, n.memoizedState = null, r;
  }
  function yo(e, n) {
    return n = Ol({ mode: "visible", children: n }, e.mode, 0, null), n.return = e, e.child = n;
  }
  function xl(e, n, t, r) {
    return r !== null && Xi(r), Tt(n, e.child, null, t), e = yo(n, n.pendingProps.children), e.flags |= 2, n.memoizedState = null, e;
  }
  function Bd(e, n, t, r, l, i, s) {
    if (t)
      return n.flags & 256 ? (n.flags &= -257, r = fo(Error(c(422))), xl(e, n, s, r)) : n.memoizedState !== null ? (n.child = e.child, n.flags |= 128, null) : (i = r.fallback, l = n.mode, r = Ol({ mode: "visible", children: r.children }, l, 0, null), i = pt(i, l, s, null), i.flags |= 2, r.return = n, i.return = n, r.sibling = i, n.child = r, (n.mode & 1) !== 0 && Tt(n, e.child, null, s), n.child.memoizedState = go(s), n.memoizedState = vo, i);
    if ((n.mode & 1) === 0) return xl(e, n, s, null);
    if (l.data === "$!") {
      if (r = l.nextSibling && l.nextSibling.dataset, r) var d = r.dgst;
      return r = d, i = Error(c(419)), r = fo(i, r, void 0), xl(e, n, s, r);
    }
    if (d = (s & e.childLanes) !== 0, be || d) {
      if (r = Ie, r !== null) {
        switch (s & -s) {
          case 4:
            l = 2;
            break;
          case 16:
            l = 8;
            break;
          case 64:
          case 128:
          case 256:
          case 512:
          case 1024:
          case 2048:
          case 4096:
          case 8192:
          case 16384:
          case 32768:
          case 65536:
          case 131072:
          case 262144:
          case 524288:
          case 1048576:
          case 2097152:
          case 4194304:
          case 8388608:
          case 16777216:
          case 33554432:
          case 67108864:
            l = 32;
            break;
          case 536870912:
            l = 268435456;
            break;
          default:
            l = 0;
        }
        l = (l & (r.suspendedLanes | s)) !== 0 ? 0 : l, l !== 0 && l !== i.retryLane && (i.retryLane = l, On(e, l), wn(r, e, l, -1));
      }
      return Mo(), r = fo(Error(c(421))), xl(e, n, s, r);
    }
    return l.data === "$?" ? (n.flags |= 128, n.child = e.child, n = tf.bind(null, e), l._reactRetry = n, null) : (e = i.treeContext, on = Hn(l.nextSibling), ln = n, he = !0, vn = null, e !== null && (un[an++] = Tn, un[an++] = Ln, un[an++] = lt, Tn = e.id, Ln = e.overflow, lt = n), n = yo(n, r.children), n.flags |= 4096, n);
  }
  function ha(e, n, t) {
    e.lanes |= n;
    var r = e.alternate;
    r !== null && (r.lanes |= n), Qi(e.return, n, t);
  }
  function xo(e, n, t, r, l) {
    var i = e.memoizedState;
    i === null ? e.memoizedState = { isBackwards: n, rendering: null, renderingStartTime: 0, last: r, tail: t, tailMode: l } : (i.isBackwards = n, i.rendering = null, i.renderingStartTime = 0, i.last = r, i.tail = t, i.tailMode = l);
  }
  function ma(e, n, t) {
    var r = n.pendingProps, l = r.revealOrder, i = r.tail;
    if (Ke(e, n, r.children, t), r = ye.current, (r & 2) !== 0) r = r & 1 | 2, n.flags |= 128;
    else {
      if (e !== null && (e.flags & 128) !== 0) e: for (e = n.child; e !== null; ) {
        if (e.tag === 13) e.memoizedState !== null && ha(e, t, n);
        else if (e.tag === 19) ha(e, t, n);
        else if (e.child !== null) {
          e.child.return = e, e = e.child;
          continue;
        }
        if (e === n) break e;
        for (; e.sibling === null; ) {
          if (e.return === null || e.return === n) break e;
          e = e.return;
        }
        e.sibling.return = e.return, e = e.sibling;
      }
      r &= 1;
    }
    if (ae(ye, r), (n.mode & 1) === 0) n.memoizedState = null;
    else switch (l) {
      case "forwards":
        for (t = n.child, l = null; t !== null; ) e = t.alternate, e !== null && fl(e) === null && (l = t), t = t.sibling;
        t = l, t === null ? (l = n.child, n.child = null) : (l = t.sibling, t.sibling = null), xo(n, !1, l, t, i);
        break;
      case "backwards":
        for (t = null, l = n.child, n.child = null; l !== null; ) {
          if (e = l.alternate, e !== null && fl(e) === null) {
            n.child = l;
            break;
          }
          e = l.sibling, l.sibling = t, t = l, l = e;
        }
        xo(n, !0, t, null, i);
        break;
      case "together":
        xo(n, !1, null, null, void 0);
        break;
      default:
        n.memoizedState = null;
    }
    return n.child;
  }
  function wl(e, n) {
    (n.mode & 1) === 0 && e !== null && (e.alternate = null, n.alternate = null, n.flags |= 2);
  }
  function Mn(e, n, t) {
    if (e !== null && (n.dependencies = e.dependencies), at |= n.lanes, (t & n.childLanes) === 0) return null;
    if (e !== null && n.child !== e.child) throw Error(c(153));
    if (n.child !== null) {
      for (e = n.child, t = $n(e, e.pendingProps), n.child = t, t.return = n; e.sibling !== null; ) e = e.sibling, t = t.sibling = $n(e, e.pendingProps), t.return = n;
      t.sibling = null;
    }
    return n.child;
  }
  function Xd(e, n, t) {
    switch (n.tag) {
      case 3:
        da(n), Pt();
        break;
      case 5:
        Pu(n);
        break;
      case 1:
        Ye(n.type) && tl(n);
        break;
      case 4:
        bi(n, n.stateNode.containerInfo);
        break;
      case 10:
        var r = n.type._context, l = n.memoizedProps.value;
        ae(ul, r._currentValue), r._currentValue = l;
        break;
      case 13:
        if (r = n.memoizedState, r !== null)
          return r.dehydrated !== null ? (ae(ye, ye.current & 1), n.flags |= 128, null) : (t & n.child.childLanes) !== 0 ? pa(e, n, t) : (ae(ye, ye.current & 1), e = Mn(e, n, t), e !== null ? e.sibling : null);
        ae(ye, ye.current & 1);
        break;
      case 19:
        if (r = (t & n.childLanes) !== 0, (e.flags & 128) !== 0) {
          if (r) return ma(e, n, t);
          n.flags |= 128;
        }
        if (l = n.memoizedState, l !== null && (l.rendering = null, l.tail = null, l.lastEffect = null), ae(ye, ye.current), r) break;
        return null;
      case 22:
      case 23:
        return n.lanes = 0, ua(e, n, t);
    }
    return Mn(e, n, t);
  }
  var va, wo, ga, ya;
  va = function(e, n) {
    for (var t = n.child; t !== null; ) {
      if (t.tag === 5 || t.tag === 6) e.appendChild(t.stateNode);
      else if (t.tag !== 4 && t.child !== null) {
        t.child.return = t, t = t.child;
        continue;
      }
      if (t === n) break;
      for (; t.sibling === null; ) {
        if (t.return === null || t.return === n) return;
        t = t.return;
      }
      t.sibling.return = t.return, t = t.sibling;
    }
  }, wo = function() {
  }, ga = function(e, n, t, r) {
    var l = e.memoizedProps;
    if (l !== r) {
      e = n.stateNode, st(Nn.current);
      var i = null;
      switch (t) {
        case "input":
          l = Ql(e, l), r = Ql(e, r), i = [];
          break;
        case "select":
          l = P({}, l, { value: void 0 }), r = P({}, r, { value: void 0 }), i = [];
          break;
        case "textarea":
          l = bl(e, l), r = bl(e, r), i = [];
          break;
        default:
          typeof l.onClick != "function" && typeof r.onClick == "function" && (e.onclick = $r);
      }
      $l(t, r);
      var s;
      t = null;
      for (y in l) if (!r.hasOwnProperty(y) && l.hasOwnProperty(y) && l[y] != null) if (y === "style") {
        var d = l[y];
        for (s in d) d.hasOwnProperty(s) && (t || (t = {}), t[s] = "");
      } else y !== "dangerouslySetInnerHTML" && y !== "children" && y !== "suppressContentEditableWarning" && y !== "suppressHydrationWarning" && y !== "autoFocus" && (w.hasOwnProperty(y) ? i || (i = []) : (i = i || []).push(y, null));
      for (y in r) {
        var f = r[y];
        if (d = l != null ? l[y] : void 0, r.hasOwnProperty(y) && f !== d && (f != null || d != null)) if (y === "style") if (d) {
          for (s in d) !d.hasOwnProperty(s) || f && f.hasOwnProperty(s) || (t || (t = {}), t[s] = "");
          for (s in f) f.hasOwnProperty(s) && d[s] !== f[s] && (t || (t = {}), t[s] = f[s]);
        } else t || (i || (i = []), i.push(
          y,
          t
        )), t = f;
        else y === "dangerouslySetInnerHTML" ? (f = f ? f.__html : void 0, d = d ? d.__html : void 0, f != null && d !== f && (i = i || []).push(y, f)) : y === "children" ? typeof f != "string" && typeof f != "number" || (i = i || []).push(y, "" + f) : y !== "suppressContentEditableWarning" && y !== "suppressHydrationWarning" && (w.hasOwnProperty(y) ? (f != null && y === "onScroll" && ce("scroll", e), i || d === f || (i = [])) : (i = i || []).push(y, f));
      }
      t && (i = i || []).push("style", t);
      var y = i;
      (n.updateQueue = y) && (n.flags |= 4);
    }
  }, ya = function(e, n, t, r) {
    t !== r && (n.flags |= 4);
  };
  function yr(e, n) {
    if (!he) switch (e.tailMode) {
      case "hidden":
        n = e.tail;
        for (var t = null; n !== null; ) n.alternate !== null && (t = n), n = n.sibling;
        t === null ? e.tail = null : t.sibling = null;
        break;
      case "collapsed":
        t = e.tail;
        for (var r = null; t !== null; ) t.alternate !== null && (r = t), t = t.sibling;
        r === null ? n || e.tail === null ? e.tail = null : e.tail.sibling = null : r.sibling = null;
    }
  }
  function Ze(e) {
    var n = e.alternate !== null && e.alternate.child === e.child, t = 0, r = 0;
    if (n) for (var l = e.child; l !== null; ) t |= l.lanes | l.childLanes, r |= l.subtreeFlags & 14680064, r |= l.flags & 14680064, l.return = e, l = l.sibling;
    else for (l = e.child; l !== null; ) t |= l.lanes | l.childLanes, r |= l.subtreeFlags, r |= l.flags, l.return = e, l = l.sibling;
    return e.subtreeFlags |= r, e.childLanes = t, n;
  }
  function Zd(e, n, t) {
    var r = n.pendingProps;
    switch (Ai(n), n.tag) {
      case 2:
      case 16:
      case 15:
      case 0:
      case 11:
      case 7:
      case 8:
      case 12:
      case 9:
      case 14:
        return Ze(n), null;
      case 1:
        return Ye(n.type) && nl(), Ze(n), null;
      case 3:
        return r = n.stateNode, Ft(), de(Ge), de(Be), eo(), r.pendingContext && (r.context = r.pendingContext, r.pendingContext = null), (e === null || e.child === null) && (ol(n) ? n.flags |= 4 : e === null || e.memoizedState.isDehydrated && (n.flags & 256) === 0 || (n.flags |= 1024, vn !== null && (Lo(vn), vn = null))), wo(e, n), Ze(n), null;
      case 5:
        _i(n);
        var l = st(pr.current);
        if (t = n.type, e !== null && n.stateNode != null) ga(e, n, t, r, l), e.ref !== n.ref && (n.flags |= 512, n.flags |= 2097152);
        else {
          if (!r) {
            if (n.stateNode === null) throw Error(c(166));
            return Ze(n), null;
          }
          if (e = st(Nn.current), ol(n)) {
            r = n.stateNode, t = n.type;
            var i = n.memoizedProps;
            switch (r[jn] = n, r[ur] = i, e = (n.mode & 1) !== 0, t) {
              case "dialog":
                ce("cancel", r), ce("close", r);
                break;
              case "iframe":
              case "object":
              case "embed":
                ce("load", r);
                break;
              case "video":
              case "audio":
                for (l = 0; l < ir.length; l++) ce(ir[l], r);
                break;
              case "source":
                ce("error", r);
                break;
              case "img":
              case "image":
              case "link":
                ce(
                  "error",
                  r
                ), ce("load", r);
                break;
              case "details":
                ce("toggle", r);
                break;
              case "input":
                _o(r, i), ce("invalid", r);
                break;
              case "select":
                r._wrapperState = { wasMultiple: !!i.multiple }, ce("invalid", r);
                break;
              case "textarea":
                ns(r, i), ce("invalid", r);
            }
            $l(t, i), l = null;
            for (var s in i) if (i.hasOwnProperty(s)) {
              var d = i[s];
              s === "children" ? typeof d == "string" ? r.textContent !== d && (i.suppressHydrationWarning !== !0 && _r(r.textContent, d, e), l = ["children", d]) : typeof d == "number" && r.textContent !== "" + d && (i.suppressHydrationWarning !== !0 && _r(
                r.textContent,
                d,
                e
              ), l = ["children", "" + d]) : w.hasOwnProperty(s) && d != null && s === "onScroll" && ce("scroll", r);
            }
            switch (t) {
              case "input":
                Pr(r), es(r, i, !0);
                break;
              case "textarea":
                Pr(r), rs(r);
                break;
              case "select":
              case "option":
                break;
              default:
                typeof i.onClick == "function" && (r.onclick = $r);
            }
            r = l, n.updateQueue = r, r !== null && (n.flags |= 4);
          } else {
            s = l.nodeType === 9 ? l : l.ownerDocument, e === "http://www.w3.org/1999/xhtml" && (e = ls(t)), e === "http://www.w3.org/1999/xhtml" ? t === "script" ? (e = s.createElement("div"), e.innerHTML = "<script><\/script>", e = e.removeChild(e.firstChild)) : typeof r.is == "string" ? e = s.createElement(t, { is: r.is }) : (e = s.createElement(t), t === "select" && (s = e, r.multiple ? s.multiple = !0 : r.size && (s.size = r.size))) : e = s.createElementNS(e, t), e[jn] = n, e[ur] = r, va(e, n, !1, !1), n.stateNode = e;
            e: {
              switch (s = ei(t, r), t) {
                case "dialog":
                  ce("cancel", e), ce("close", e), l = r;
                  break;
                case "iframe":
                case "object":
                case "embed":
                  ce("load", e), l = r;
                  break;
                case "video":
                case "audio":
                  for (l = 0; l < ir.length; l++) ce(ir[l], e);
                  l = r;
                  break;
                case "source":
                  ce("error", e), l = r;
                  break;
                case "img":
                case "image":
                case "link":
                  ce(
                    "error",
                    e
                  ), ce("load", e), l = r;
                  break;
                case "details":
                  ce("toggle", e), l = r;
                  break;
                case "input":
                  _o(e, r), l = Ql(e, r), ce("invalid", e);
                  break;
                case "option":
                  l = r;
                  break;
                case "select":
                  e._wrapperState = { wasMultiple: !!r.multiple }, l = P({}, r, { value: void 0 }), ce("invalid", e);
                  break;
                case "textarea":
                  ns(e, r), l = bl(e, r), ce("invalid", e);
                  break;
                default:
                  l = r;
              }
              $l(t, l), d = l;
              for (i in d) if (d.hasOwnProperty(i)) {
                var f = d[i];
                i === "style" ? ss(e, f) : i === "dangerouslySetInnerHTML" ? (f = f ? f.__html : void 0, f != null && is(e, f)) : i === "children" ? typeof f == "string" ? (t !== "textarea" || f !== "") && qt(e, f) : typeof f == "number" && qt(e, "" + f) : i !== "suppressContentEditableWarning" && i !== "suppressHydrationWarning" && i !== "autoFocus" && (w.hasOwnProperty(i) ? f != null && i === "onScroll" && ce("scroll", e) : f != null && fe(e, i, f, s));
              }
              switch (t) {
                case "input":
                  Pr(e), es(e, r, !1);
                  break;
                case "textarea":
                  Pr(e), rs(e);
                  break;
                case "option":
                  r.value != null && e.setAttribute("value", "" + b(r.value));
                  break;
                case "select":
                  e.multiple = !!r.multiple, i = r.value, i != null ? ht(e, !!r.multiple, i, !1) : r.defaultValue != null && ht(
                    e,
                    !!r.multiple,
                    r.defaultValue,
                    !0
                  );
                  break;
                default:
                  typeof l.onClick == "function" && (e.onclick = $r);
              }
              switch (t) {
                case "button":
                case "input":
                case "select":
                case "textarea":
                  r = !!r.autoFocus;
                  break e;
                case "img":
                  r = !0;
                  break e;
                default:
                  r = !1;
              }
            }
            r && (n.flags |= 4);
          }
          n.ref !== null && (n.flags |= 512, n.flags |= 2097152);
        }
        return Ze(n), null;
      case 6:
        if (e && n.stateNode != null) ya(e, n, e.memoizedProps, r);
        else {
          if (typeof r != "string" && n.stateNode === null) throw Error(c(166));
          if (t = st(pr.current), st(Nn.current), ol(n)) {
            if (r = n.stateNode, t = n.memoizedProps, r[jn] = n, (i = r.nodeValue !== t) && (e = ln, e !== null)) switch (e.tag) {
              case 3:
                _r(r.nodeValue, t, (e.mode & 1) !== 0);
                break;
              case 5:
                e.memoizedProps.suppressHydrationWarning !== !0 && _r(r.nodeValue, t, (e.mode & 1) !== 0);
            }
            i && (n.flags |= 4);
          } else r = (t.nodeType === 9 ? t : t.ownerDocument).createTextNode(r), r[jn] = n, n.stateNode = r;
        }
        return Ze(n), null;
      case 13:
        if (de(ye), r = n.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
          if (he && on !== null && (n.mode & 1) !== 0 && (n.flags & 128) === 0) ku(), Pt(), n.flags |= 98560, i = !1;
          else if (i = ol(n), r !== null && r.dehydrated !== null) {
            if (e === null) {
              if (!i) throw Error(c(318));
              if (i = n.memoizedState, i = i !== null ? i.dehydrated : null, !i) throw Error(c(317));
              i[jn] = n;
            } else Pt(), (n.flags & 128) === 0 && (n.memoizedState = null), n.flags |= 4;
            Ze(n), i = !1;
          } else vn !== null && (Lo(vn), vn = null), i = !0;
          if (!i) return n.flags & 65536 ? n : null;
        }
        return (n.flags & 128) !== 0 ? (n.lanes = t, n) : (r = r !== null, r !== (e !== null && e.memoizedState !== null) && r && (n.child.flags |= 8192, (n.mode & 1) !== 0 && (e === null || (ye.current & 1) !== 0 ? Oe === 0 && (Oe = 3) : Mo())), n.updateQueue !== null && (n.flags |= 4), Ze(n), null);
      case 4:
        return Ft(), wo(e, n), e === null && or(n.stateNode.containerInfo), Ze(n), null;
      case 10:
        return Ki(n.type._context), Ze(n), null;
      case 17:
        return Ye(n.type) && nl(), Ze(n), null;
      case 19:
        if (de(ye), i = n.memoizedState, i === null) return Ze(n), null;
        if (r = (n.flags & 128) !== 0, s = i.rendering, s === null) if (r) yr(i, !1);
        else {
          if (Oe !== 0 || e !== null && (e.flags & 128) !== 0) for (e = n.child; e !== null; ) {
            if (s = fl(e), s !== null) {
              for (n.flags |= 128, yr(i, !1), r = s.updateQueue, r !== null && (n.updateQueue = r, n.flags |= 4), n.subtreeFlags = 0, r = t, t = n.child; t !== null; ) i = t, e = r, i.flags &= 14680066, s = i.alternate, s === null ? (i.childLanes = 0, i.lanes = e, i.child = null, i.subtreeFlags = 0, i.memoizedProps = null, i.memoizedState = null, i.updateQueue = null, i.dependencies = null, i.stateNode = null) : (i.childLanes = s.childLanes, i.lanes = s.lanes, i.child = s.child, i.subtreeFlags = 0, i.deletions = null, i.memoizedProps = s.memoizedProps, i.memoizedState = s.memoizedState, i.updateQueue = s.updateQueue, i.type = s.type, e = s.dependencies, i.dependencies = e === null ? null : { lanes: e.lanes, firstContext: e.firstContext }), t = t.sibling;
              return ae(ye, ye.current & 1 | 2), n.child;
            }
            e = e.sibling;
          }
          i.tail !== null && je() > Dt && (n.flags |= 128, r = !0, yr(i, !1), n.lanes = 4194304);
        }
        else {
          if (!r) if (e = fl(s), e !== null) {
            if (n.flags |= 128, r = !0, t = e.updateQueue, t !== null && (n.updateQueue = t, n.flags |= 4), yr(i, !0), i.tail === null && i.tailMode === "hidden" && !s.alternate && !he) return Ze(n), null;
          } else 2 * je() - i.renderingStartTime > Dt && t !== 1073741824 && (n.flags |= 128, r = !0, yr(i, !1), n.lanes = 4194304);
          i.isBackwards ? (s.sibling = n.child, n.child = s) : (t = i.last, t !== null ? t.sibling = s : n.child = s, i.last = s);
        }
        return i.tail !== null ? (n = i.tail, i.rendering = n, i.tail = n.sibling, i.renderingStartTime = je(), n.sibling = null, t = ye.current, ae(ye, r ? t & 1 | 2 : t & 1), n) : (Ze(n), null);
      case 22:
      case 23:
        return Fo(), r = n.memoizedState !== null, e !== null && e.memoizedState !== null !== r && (n.flags |= 8192), r && (n.mode & 1) !== 0 ? (sn & 1073741824) !== 0 && (Ze(n), n.subtreeFlags & 6 && (n.flags |= 8192)) : Ze(n), null;
      case 24:
        return null;
      case 25:
        return null;
    }
    throw Error(c(156, n.tag));
  }
  function Jd(e, n) {
    switch (Ai(n), n.tag) {
      case 1:
        return Ye(n.type) && nl(), e = n.flags, e & 65536 ? (n.flags = e & -65537 | 128, n) : null;
      case 3:
        return Ft(), de(Ge), de(Be), eo(), e = n.flags, (e & 65536) !== 0 && (e & 128) === 0 ? (n.flags = e & -65537 | 128, n) : null;
      case 5:
        return _i(n), null;
      case 13:
        if (de(ye), e = n.memoizedState, e !== null && e.dehydrated !== null) {
          if (n.alternate === null) throw Error(c(340));
          Pt();
        }
        return e = n.flags, e & 65536 ? (n.flags = e & -65537 | 128, n) : null;
      case 19:
        return de(ye), null;
      case 4:
        return Ft(), null;
      case 10:
        return Ki(n.type._context), null;
      case 22:
      case 23:
        return Fo(), null;
      case 24:
        return null;
      default:
        return null;
    }
  }
  var kl = !1, Je = !1, Kd = typeof WeakSet == "function" ? WeakSet : Set, I = null;
  function It(e, n) {
    var t = e.ref;
    if (t !== null) if (typeof t == "function") try {
      t(null);
    } catch (r) {
      ke(e, n, r);
    }
    else t.current = null;
  }
  function ko(e, n, t) {
    try {
      t();
    } catch (r) {
      ke(e, n, r);
    }
  }
  var xa = !1;
  function Qd(e, n) {
    if (Oi = Ar, e = bs(), Ni(e)) {
      if ("selectionStart" in e) var t = { start: e.selectionStart, end: e.selectionEnd };
      else e: {
        t = (t = e.ownerDocument) && t.defaultView || window;
        var r = t.getSelection && t.getSelection();
        if (r && r.rangeCount !== 0) {
          t = r.anchorNode;
          var l = r.anchorOffset, i = r.focusNode;
          r = r.focusOffset;
          try {
            t.nodeType, i.nodeType;
          } catch {
            t = null;
            break e;
          }
          var s = 0, d = -1, f = -1, y = 0, N = 0, C = e, j = null;
          n: for (; ; ) {
            for (var F; C !== t || l !== 0 && C.nodeType !== 3 || (d = s + l), C !== i || r !== 0 && C.nodeType !== 3 || (f = s + r), C.nodeType === 3 && (s += C.nodeValue.length), (F = C.firstChild) !== null; )
              j = C, C = F;
            for (; ; ) {
              if (C === e) break n;
              if (j === t && ++y === l && (d = s), j === i && ++N === r && (f = s), (F = C.nextSibling) !== null) break;
              C = j, j = C.parentNode;
            }
            C = F;
          }
          t = d === -1 || f === -1 ? null : { start: d, end: f };
        } else t = null;
      }
      t = t || { start: 0, end: 0 };
    } else t = null;
    for (Fi = { focusedElem: e, selectionRange: t }, Ar = !1, I = n; I !== null; ) if (n = I, e = n.child, (n.subtreeFlags & 1028) !== 0 && e !== null) e.return = n, I = e;
    else for (; I !== null; ) {
      n = I;
      try {
        var W = n.alternate;
        if ((n.flags & 1024) !== 0) switch (n.tag) {
          case 0:
          case 11:
          case 15:
            break;
          case 1:
            if (W !== null) {
              var D = W.memoizedProps, Ne = W.memoizedState, m = n.stateNode, p = m.getSnapshotBeforeUpdate(n.elementType === n.type ? D : gn(n.type, D), Ne);
              m.__reactInternalSnapshotBeforeUpdate = p;
            }
            break;
          case 3:
            var g = n.stateNode.containerInfo;
            g.nodeType === 1 ? g.textContent = "" : g.nodeType === 9 && g.documentElement && g.removeChild(g.documentElement);
            break;
          case 5:
          case 6:
          case 4:
          case 17:
            break;
          default:
            throw Error(c(163));
        }
      } catch (L) {
        ke(n, n.return, L);
      }
      if (e = n.sibling, e !== null) {
        e.return = n.return, I = e;
        break;
      }
      I = n.return;
    }
    return W = xa, xa = !1, W;
  }
  function xr(e, n, t) {
    var r = n.updateQueue;
    if (r = r !== null ? r.lastEffect : null, r !== null) {
      var l = r = r.next;
      do {
        if ((l.tag & e) === e) {
          var i = l.destroy;
          l.destroy = void 0, i !== void 0 && ko(n, t, i);
        }
        l = l.next;
      } while (l !== r);
    }
  }
  function Sl(e, n) {
    if (n = n.updateQueue, n = n !== null ? n.lastEffect : null, n !== null) {
      var t = n = n.next;
      do {
        if ((t.tag & e) === e) {
          var r = t.create;
          t.destroy = r();
        }
        t = t.next;
      } while (t !== n);
    }
  }
  function So(e) {
    var n = e.ref;
    if (n !== null) {
      var t = e.stateNode;
      switch (e.tag) {
        case 5:
          e = t;
          break;
        default:
          e = t;
      }
      typeof n == "function" ? n(e) : n.current = e;
    }
  }
  function wa(e) {
    var n = e.alternate;
    n !== null && (e.alternate = null, wa(n)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (n = e.stateNode, n !== null && (delete n[jn], delete n[ur], delete n[Di], delete n[Td], delete n[Ld])), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
  }
  function ka(e) {
    return e.tag === 5 || e.tag === 3 || e.tag === 4;
  }
  function Sa(e) {
    e: for (; ; ) {
      for (; e.sibling === null; ) {
        if (e.return === null || ka(e.return)) return null;
        e = e.return;
      }
      for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18; ) {
        if (e.flags & 2 || e.child === null || e.tag === 4) continue e;
        e.child.return = e, e = e.child;
      }
      if (!(e.flags & 2)) return e.stateNode;
    }
  }
  function jo(e, n, t) {
    var r = e.tag;
    if (r === 5 || r === 6) e = e.stateNode, n ? t.nodeType === 8 ? t.parentNode.insertBefore(e, n) : t.insertBefore(e, n) : (t.nodeType === 8 ? (n = t.parentNode, n.insertBefore(e, t)) : (n = t, n.appendChild(e)), t = t._reactRootContainer, t != null || n.onclick !== null || (n.onclick = $r));
    else if (r !== 4 && (e = e.child, e !== null)) for (jo(e, n, t), e = e.sibling; e !== null; ) jo(e, n, t), e = e.sibling;
  }
  function No(e, n, t) {
    var r = e.tag;
    if (r === 5 || r === 6) e = e.stateNode, n ? t.insertBefore(e, n) : t.appendChild(e);
    else if (r !== 4 && (e = e.child, e !== null)) for (No(e, n, t), e = e.sibling; e !== null; ) No(e, n, t), e = e.sibling;
  }
  var Ue = null, yn = !1;
  function Qn(e, n, t) {
    for (t = t.child; t !== null; ) ja(e, n, t), t = t.sibling;
  }
  function ja(e, n, t) {
    if (Sn && typeof Sn.onCommitFiberUnmount == "function") try {
      Sn.onCommitFiberUnmount(Ir, t);
    } catch {
    }
    switch (t.tag) {
      case 5:
        Je || It(t, n);
      case 6:
        var r = Ue, l = yn;
        Ue = null, Qn(e, n, t), Ue = r, yn = l, Ue !== null && (yn ? (e = Ue, t = t.stateNode, e.nodeType === 8 ? e.parentNode.removeChild(t) : e.removeChild(t)) : Ue.removeChild(t.stateNode));
        break;
      case 18:
        Ue !== null && (yn ? (e = Ue, t = t.stateNode, e.nodeType === 8 ? Wi(e.parentNode, t) : e.nodeType === 1 && Wi(e, t), bt(e)) : Wi(Ue, t.stateNode));
        break;
      case 4:
        r = Ue, l = yn, Ue = t.stateNode.containerInfo, yn = !0, Qn(e, n, t), Ue = r, yn = l;
        break;
      case 0:
      case 11:
      case 14:
      case 15:
        if (!Je && (r = t.updateQueue, r !== null && (r = r.lastEffect, r !== null))) {
          l = r = r.next;
          do {
            var i = l, s = i.destroy;
            i = i.tag, s !== void 0 && ((i & 2) !== 0 || (i & 4) !== 0) && ko(t, n, s), l = l.next;
          } while (l !== r);
        }
        Qn(e, n, t);
        break;
      case 1:
        if (!Je && (It(t, n), r = t.stateNode, typeof r.componentWillUnmount == "function")) try {
          r.props = t.memoizedProps, r.state = t.memoizedState, r.componentWillUnmount();
        } catch (d) {
          ke(t, n, d);
        }
        Qn(e, n, t);
        break;
      case 21:
        Qn(e, n, t);
        break;
      case 22:
        t.mode & 1 ? (Je = (r = Je) || t.memoizedState !== null, Qn(e, n, t), Je = r) : Qn(e, n, t);
        break;
      default:
        Qn(e, n, t);
    }
  }
  function Na(e) {
    var n = e.updateQueue;
    if (n !== null) {
      e.updateQueue = null;
      var t = e.stateNode;
      t === null && (t = e.stateNode = new Kd()), n.forEach(function(r) {
        var l = rf.bind(null, e, r);
        t.has(r) || (t.add(r), r.then(l, l));
      });
    }
  }
  function xn(e, n) {
    var t = n.deletions;
    if (t !== null) for (var r = 0; r < t.length; r++) {
      var l = t[r];
      try {
        var i = e, s = n, d = s;
        e: for (; d !== null; ) {
          switch (d.tag) {
            case 5:
              Ue = d.stateNode, yn = !1;
              break e;
            case 3:
              Ue = d.stateNode.containerInfo, yn = !0;
              break e;
            case 4:
              Ue = d.stateNode.containerInfo, yn = !0;
              break e;
          }
          d = d.return;
        }
        if (Ue === null) throw Error(c(160));
        ja(i, s, l), Ue = null, yn = !1;
        var f = l.alternate;
        f !== null && (f.return = null), l.return = null;
      } catch (y) {
        ke(l, n, y);
      }
    }
    if (n.subtreeFlags & 12854) for (n = n.child; n !== null; ) Ca(n, e), n = n.sibling;
  }
  function Ca(e, n) {
    var t = e.alternate, r = e.flags;
    switch (e.tag) {
      case 0:
      case 11:
      case 14:
      case 15:
        if (xn(n, e), En(e), r & 4) {
          try {
            xr(3, e, e.return), Sl(3, e);
          } catch (D) {
            ke(e, e.return, D);
          }
          try {
            xr(5, e, e.return);
          } catch (D) {
            ke(e, e.return, D);
          }
        }
        break;
      case 1:
        xn(n, e), En(e), r & 512 && t !== null && It(t, t.return);
        break;
      case 5:
        if (xn(n, e), En(e), r & 512 && t !== null && It(t, t.return), e.flags & 32) {
          var l = e.stateNode;
          try {
            qt(l, "");
          } catch (D) {
            ke(e, e.return, D);
          }
        }
        if (r & 4 && (l = e.stateNode, l != null)) {
          var i = e.memoizedProps, s = t !== null ? t.memoizedProps : i, d = e.type, f = e.updateQueue;
          if (e.updateQueue = null, f !== null) try {
            d === "input" && i.type === "radio" && i.name != null && $o(l, i), ei(d, s);
            var y = ei(d, i);
            for (s = 0; s < f.length; s += 2) {
              var N = f[s], C = f[s + 1];
              N === "style" ? ss(l, C) : N === "dangerouslySetInnerHTML" ? is(l, C) : N === "children" ? qt(l, C) : fe(l, N, C, y);
            }
            switch (d) {
              case "input":
                Gl(l, i);
                break;
              case "textarea":
                ts(l, i);
                break;
              case "select":
                var j = l._wrapperState.wasMultiple;
                l._wrapperState.wasMultiple = !!i.multiple;
                var F = i.value;
                F != null ? ht(l, !!i.multiple, F, !1) : j !== !!i.multiple && (i.defaultValue != null ? ht(
                  l,
                  !!i.multiple,
                  i.defaultValue,
                  !0
                ) : ht(l, !!i.multiple, i.multiple ? [] : "", !1));
            }
            l[ur] = i;
          } catch (D) {
            ke(e, e.return, D);
          }
        }
        break;
      case 6:
        if (xn(n, e), En(e), r & 4) {
          if (e.stateNode === null) throw Error(c(162));
          l = e.stateNode, i = e.memoizedProps;
          try {
            l.nodeValue = i;
          } catch (D) {
            ke(e, e.return, D);
          }
        }
        break;
      case 3:
        if (xn(n, e), En(e), r & 4 && t !== null && t.memoizedState.isDehydrated) try {
          bt(n.containerInfo);
        } catch (D) {
          ke(e, e.return, D);
        }
        break;
      case 4:
        xn(n, e), En(e);
        break;
      case 13:
        xn(n, e), En(e), l = e.child, l.flags & 8192 && (i = l.memoizedState !== null, l.stateNode.isHidden = i, !i || l.alternate !== null && l.alternate.memoizedState !== null || (Ro = je())), r & 4 && Na(e);
        break;
      case 22:
        if (N = t !== null && t.memoizedState !== null, e.mode & 1 ? (Je = (y = Je) || N, xn(n, e), Je = y) : xn(n, e), En(e), r & 8192) {
          if (y = e.memoizedState !== null, (e.stateNode.isHidden = y) && !N && (e.mode & 1) !== 0) for (I = e, N = e.child; N !== null; ) {
            for (C = I = N; I !== null; ) {
              switch (j = I, F = j.child, j.tag) {
                case 0:
                case 11:
                case 14:
                case 15:
                  xr(4, j, j.return);
                  break;
                case 1:
                  It(j, j.return);
                  var W = j.stateNode;
                  if (typeof W.componentWillUnmount == "function") {
                    r = j, t = j.return;
                    try {
                      n = r, W.props = n.memoizedProps, W.state = n.memoizedState, W.componentWillUnmount();
                    } catch (D) {
                      ke(r, t, D);
                    }
                  }
                  break;
                case 5:
                  It(j, j.return);
                  break;
                case 22:
                  if (j.memoizedState !== null) {
                    za(C);
                    continue;
                  }
              }
              F !== null ? (F.return = j, I = F) : za(C);
            }
            N = N.sibling;
          }
          e: for (N = null, C = e; ; ) {
            if (C.tag === 5) {
              if (N === null) {
                N = C;
                try {
                  l = C.stateNode, y ? (i = l.style, typeof i.setProperty == "function" ? i.setProperty("display", "none", "important") : i.display = "none") : (d = C.stateNode, f = C.memoizedProps.style, s = f != null && f.hasOwnProperty("display") ? f.display : null, d.style.display = os("display", s));
                } catch (D) {
                  ke(e, e.return, D);
                }
              }
            } else if (C.tag === 6) {
              if (N === null) try {
                C.stateNode.nodeValue = y ? "" : C.memoizedProps;
              } catch (D) {
                ke(e, e.return, D);
              }
            } else if ((C.tag !== 22 && C.tag !== 23 || C.memoizedState === null || C === e) && C.child !== null) {
              C.child.return = C, C = C.child;
              continue;
            }
            if (C === e) break e;
            for (; C.sibling === null; ) {
              if (C.return === null || C.return === e) break e;
              N === C && (N = null), C = C.return;
            }
            N === C && (N = null), C.sibling.return = C.return, C = C.sibling;
          }
        }
        break;
      case 19:
        xn(n, e), En(e), r & 4 && Na(e);
        break;
      case 21:
        break;
      default:
        xn(
          n,
          e
        ), En(e);
    }
  }
  function En(e) {
    var n = e.flags;
    if (n & 2) {
      try {
        e: {
          for (var t = e.return; t !== null; ) {
            if (ka(t)) {
              var r = t;
              break e;
            }
            t = t.return;
          }
          throw Error(c(160));
        }
        switch (r.tag) {
          case 5:
            var l = r.stateNode;
            r.flags & 32 && (qt(l, ""), r.flags &= -33);
            var i = Sa(e);
            No(e, i, l);
            break;
          case 3:
          case 4:
            var s = r.stateNode.containerInfo, d = Sa(e);
            jo(e, d, s);
            break;
          default:
            throw Error(c(161));
        }
      } catch (f) {
        ke(e, e.return, f);
      }
      e.flags &= -3;
    }
    n & 4096 && (e.flags &= -4097);
  }
  function Gd(e, n, t) {
    I = e, Ea(e);
  }
  function Ea(e, n, t) {
    for (var r = (e.mode & 1) !== 0; I !== null; ) {
      var l = I, i = l.child;
      if (l.tag === 22 && r) {
        var s = l.memoizedState !== null || kl;
        if (!s) {
          var d = l.alternate, f = d !== null && d.memoizedState !== null || Je;
          d = kl;
          var y = Je;
          if (kl = s, (Je = f) && !y) for (I = l; I !== null; ) s = I, f = s.child, s.tag === 22 && s.memoizedState !== null ? Pa(l) : f !== null ? (f.return = s, I = f) : Pa(l);
          for (; i !== null; ) I = i, Ea(i), i = i.sibling;
          I = l, kl = d, Je = y;
        }
        Ra(e);
      } else (l.subtreeFlags & 8772) !== 0 && i !== null ? (i.return = l, I = i) : Ra(e);
    }
  }
  function Ra(e) {
    for (; I !== null; ) {
      var n = I;
      if ((n.flags & 8772) !== 0) {
        var t = n.alternate;
        try {
          if ((n.flags & 8772) !== 0) switch (n.tag) {
            case 0:
            case 11:
            case 15:
              Je || Sl(5, n);
              break;
            case 1:
              var r = n.stateNode;
              if (n.flags & 4 && !Je) if (t === null) r.componentDidMount();
              else {
                var l = n.elementType === n.type ? t.memoizedProps : gn(n.type, t.memoizedProps);
                r.componentDidUpdate(l, t.memoizedState, r.__reactInternalSnapshotBeforeUpdate);
              }
              var i = n.updateQueue;
              i !== null && zu(n, i, r);
              break;
            case 3:
              var s = n.updateQueue;
              if (s !== null) {
                if (t = null, n.child !== null) switch (n.child.tag) {
                  case 5:
                    t = n.child.stateNode;
                    break;
                  case 1:
                    t = n.child.stateNode;
                }
                zu(n, s, t);
              }
              break;
            case 5:
              var d = n.stateNode;
              if (t === null && n.flags & 4) {
                t = d;
                var f = n.memoizedProps;
                switch (n.type) {
                  case "button":
                  case "input":
                  case "select":
                  case "textarea":
                    f.autoFocus && t.focus();
                    break;
                  case "img":
                    f.src && (t.src = f.src);
                }
              }
              break;
            case 6:
              break;
            case 4:
              break;
            case 12:
              break;
            case 13:
              if (n.memoizedState === null) {
                var y = n.alternate;
                if (y !== null) {
                  var N = y.memoizedState;
                  if (N !== null) {
                    var C = N.dehydrated;
                    C !== null && bt(C);
                  }
                }
              }
              break;
            case 19:
            case 17:
            case 21:
            case 22:
            case 23:
            case 25:
              break;
            default:
              throw Error(c(163));
          }
          Je || n.flags & 512 && So(n);
        } catch (j) {
          ke(n, n.return, j);
        }
      }
      if (n === e) {
        I = null;
        break;
      }
      if (t = n.sibling, t !== null) {
        t.return = n.return, I = t;
        break;
      }
      I = n.return;
    }
  }
  function za(e) {
    for (; I !== null; ) {
      var n = I;
      if (n === e) {
        I = null;
        break;
      }
      var t = n.sibling;
      if (t !== null) {
        t.return = n.return, I = t;
        break;
      }
      I = n.return;
    }
  }
  function Pa(e) {
    for (; I !== null; ) {
      var n = I;
      try {
        switch (n.tag) {
          case 0:
          case 11:
          case 15:
            var t = n.return;
            try {
              Sl(4, n);
            } catch (f) {
              ke(n, t, f);
            }
            break;
          case 1:
            var r = n.stateNode;
            if (typeof r.componentDidMount == "function") {
              var l = n.return;
              try {
                r.componentDidMount();
              } catch (f) {
                ke(n, l, f);
              }
            }
            var i = n.return;
            try {
              So(n);
            } catch (f) {
              ke(n, i, f);
            }
            break;
          case 5:
            var s = n.return;
            try {
              So(n);
            } catch (f) {
              ke(n, s, f);
            }
        }
      } catch (f) {
        ke(n, n.return, f);
      }
      if (n === e) {
        I = null;
        break;
      }
      var d = n.sibling;
      if (d !== null) {
        d.return = n.return, I = d;
        break;
      }
      I = n.return;
    }
  }
  var Yd = Math.ceil, jl = ve.ReactCurrentDispatcher, Co = ve.ReactCurrentOwner, fn = ve.ReactCurrentBatchConfig, te = 0, Ie = null, Ee = null, qe = 0, sn = 0, Wt = Bn(0), Oe = 0, wr = null, at = 0, Nl = 0, Eo = 0, kr = null, _e = null, Ro = 0, Dt = 1 / 0, In = null, Cl = !1, zo = null, Gn = null, El = !1, Yn = null, Rl = 0, Sr = 0, Po = null, zl = -1, Pl = 0;
  function Qe() {
    return (te & 6) !== 0 ? je() : zl !== -1 ? zl : zl = je();
  }
  function bn(e) {
    return (e.mode & 1) === 0 ? 1 : (te & 2) !== 0 && qe !== 0 ? qe & -qe : Fd.transition !== null ? (Pl === 0 && (Pl = Ss()), Pl) : (e = ie, e !== 0 || (e = window.event, e = e === void 0 ? 16 : Ls(e.type)), e);
  }
  function wn(e, n, t, r) {
    if (50 < Sr) throw Sr = 0, Po = null, Error(c(185));
    Jt(e, t, r), ((te & 2) === 0 || e !== Ie) && (e === Ie && ((te & 2) === 0 && (Nl |= t), Oe === 4 && _n(e, qe)), $e(e, r), t === 1 && te === 0 && (n.mode & 1) === 0 && (Dt = je() + 500, rl && Zn()));
  }
  function $e(e, n) {
    var t = e.callbackNode;
    Fc(e, n);
    var r = Vr(e, e === Ie ? qe : 0);
    if (r === 0) t !== null && xs(t), e.callbackNode = null, e.callbackPriority = 0;
    else if (n = r & -r, e.callbackPriority !== n) {
      if (t != null && xs(t), n === 1) e.tag === 0 ? Od(La.bind(null, e)) : vu(La.bind(null, e)), zd(function() {
        (te & 6) === 0 && Zn();
      }), t = null;
      else {
        switch (js(r)) {
          case 1:
            t = si;
            break;
          case 4:
            t = ws;
            break;
          case 16:
            t = Mr;
            break;
          case 536870912:
            t = ks;
            break;
          default:
            t = Mr;
        }
        t = Ua(t, Ta.bind(null, e));
      }
      e.callbackPriority = n, e.callbackNode = t;
    }
  }
  function Ta(e, n) {
    if (zl = -1, Pl = 0, (te & 6) !== 0) throw Error(c(327));
    var t = e.callbackNode;
    if (Vt() && e.callbackNode !== t) return null;
    var r = Vr(e, e === Ie ? qe : 0);
    if (r === 0) return null;
    if ((r & 30) !== 0 || (r & e.expiredLanes) !== 0 || n) n = Tl(e, r);
    else {
      n = r;
      var l = te;
      te |= 2;
      var i = Fa();
      (Ie !== e || qe !== n) && (In = null, Dt = je() + 500, dt(e, n));
      do
        try {
          $d();
          break;
        } catch (d) {
          Oa(e, d);
        }
      while (!0);
      Ji(), jl.current = i, te = l, Ee !== null ? n = 0 : (Ie = null, qe = 0, n = Oe);
    }
    if (n !== 0) {
      if (n === 2 && (l = ui(e), l !== 0 && (r = l, n = To(e, l))), n === 1) throw t = wr, dt(e, 0), _n(e, r), $e(e, je()), t;
      if (n === 6) _n(e, r);
      else {
        if (l = e.current.alternate, (r & 30) === 0 && !bd(l) && (n = Tl(e, r), n === 2 && (i = ui(e), i !== 0 && (r = i, n = To(e, i))), n === 1)) throw t = wr, dt(e, 0), _n(e, r), $e(e, je()), t;
        switch (e.finishedWork = l, e.finishedLanes = r, n) {
          case 0:
          case 1:
            throw Error(c(345));
          case 2:
            ft(e, _e, In);
            break;
          case 3:
            if (_n(e, r), (r & 130023424) === r && (n = Ro + 500 - je(), 10 < n)) {
              if (Vr(e, 0) !== 0) break;
              if (l = e.suspendedLanes, (l & r) !== r) {
                Qe(), e.pingedLanes |= e.suspendedLanes & l;
                break;
              }
              e.timeoutHandle = Ii(ft.bind(null, e, _e, In), n);
              break;
            }
            ft(e, _e, In);
            break;
          case 4:
            if (_n(e, r), (r & 4194240) === r) break;
            for (n = e.eventTimes, l = -1; 0 < r; ) {
              var s = 31 - hn(r);
              i = 1 << s, s = n[s], s > l && (l = s), r &= ~i;
            }
            if (r = l, r = je() - r, r = (120 > r ? 120 : 480 > r ? 480 : 1080 > r ? 1080 : 1920 > r ? 1920 : 3e3 > r ? 3e3 : 4320 > r ? 4320 : 1960 * Yd(r / 1960)) - r, 10 < r) {
              e.timeoutHandle = Ii(ft.bind(null, e, _e, In), r);
              break;
            }
            ft(e, _e, In);
            break;
          case 5:
            ft(e, _e, In);
            break;
          default:
            throw Error(c(329));
        }
      }
    }
    return $e(e, je()), e.callbackNode === t ? Ta.bind(null, e) : null;
  }
  function To(e, n) {
    var t = kr;
    return e.current.memoizedState.isDehydrated && (dt(e, n).flags |= 256), e = Tl(e, n), e !== 2 && (n = _e, _e = t, n !== null && Lo(n)), e;
  }
  function Lo(e) {
    _e === null ? _e = e : _e.push.apply(_e, e);
  }
  function bd(e) {
    for (var n = e; ; ) {
      if (n.flags & 16384) {
        var t = n.updateQueue;
        if (t !== null && (t = t.stores, t !== null)) for (var r = 0; r < t.length; r++) {
          var l = t[r], i = l.getSnapshot;
          l = l.value;
          try {
            if (!mn(i(), l)) return !1;
          } catch {
            return !1;
          }
        }
      }
      if (t = n.child, n.subtreeFlags & 16384 && t !== null) t.return = n, n = t;
      else {
        if (n === e) break;
        for (; n.sibling === null; ) {
          if (n.return === null || n.return === e) return !0;
          n = n.return;
        }
        n.sibling.return = n.return, n = n.sibling;
      }
    }
    return !0;
  }
  function _n(e, n) {
    for (n &= ~Eo, n &= ~Nl, e.suspendedLanes |= n, e.pingedLanes &= ~n, e = e.expirationTimes; 0 < n; ) {
      var t = 31 - hn(n), r = 1 << t;
      e[t] = -1, n &= ~r;
    }
  }
  function La(e) {
    if ((te & 6) !== 0) throw Error(c(327));
    Vt();
    var n = Vr(e, 0);
    if ((n & 1) === 0) return $e(e, je()), null;
    var t = Tl(e, n);
    if (e.tag !== 0 && t === 2) {
      var r = ui(e);
      r !== 0 && (n = r, t = To(e, r));
    }
    if (t === 1) throw t = wr, dt(e, 0), _n(e, n), $e(e, je()), t;
    if (t === 6) throw Error(c(345));
    return e.finishedWork = e.current.alternate, e.finishedLanes = n, ft(e, _e, In), $e(e, je()), null;
  }
  function Oo(e, n) {
    var t = te;
    te |= 1;
    try {
      return e(n);
    } finally {
      te = t, te === 0 && (Dt = je() + 500, rl && Zn());
    }
  }
  function ct(e) {
    Yn !== null && Yn.tag === 0 && (te & 6) === 0 && Vt();
    var n = te;
    te |= 1;
    var t = fn.transition, r = ie;
    try {
      if (fn.transition = null, ie = 1, e) return e();
    } finally {
      ie = r, fn.transition = t, te = n, (te & 6) === 0 && Zn();
    }
  }
  function Fo() {
    sn = Wt.current, de(Wt);
  }
  function dt(e, n) {
    e.finishedWork = null, e.finishedLanes = 0;
    var t = e.timeoutHandle;
    if (t !== -1 && (e.timeoutHandle = -1, Rd(t)), Ee !== null) for (t = Ee.return; t !== null; ) {
      var r = t;
      switch (Ai(r), r.tag) {
        case 1:
          r = r.type.childContextTypes, r != null && nl();
          break;
        case 3:
          Ft(), de(Ge), de(Be), eo();
          break;
        case 5:
          _i(r);
          break;
        case 4:
          Ft();
          break;
        case 13:
          de(ye);
          break;
        case 19:
          de(ye);
          break;
        case 10:
          Ki(r.type._context);
          break;
        case 22:
        case 23:
          Fo();
      }
      t = t.return;
    }
    if (Ie = e, Ee = e = $n(e.current, null), qe = sn = n, Oe = 0, wr = null, Eo = Nl = at = 0, _e = kr = null, ot !== null) {
      for (n = 0; n < ot.length; n++) if (t = ot[n], r = t.interleaved, r !== null) {
        t.interleaved = null;
        var l = r.next, i = t.pending;
        if (i !== null) {
          var s = i.next;
          i.next = l, r.next = s;
        }
        t.pending = r;
      }
      ot = null;
    }
    return e;
  }
  function Oa(e, n) {
    do {
      var t = Ee;
      try {
        if (Ji(), pl.current = gl, hl) {
          for (var r = xe.memoizedState; r !== null; ) {
            var l = r.queue;
            l !== null && (l.pending = null), r = r.next;
          }
          hl = !1;
        }
        if (ut = 0, Me = Le = xe = null, hr = !1, mr = 0, Co.current = null, t === null || t.return === null) {
          Oe = 1, wr = n, Ee = null;
          break;
        }
        e: {
          var i = e, s = t.return, d = t, f = n;
          if (n = qe, d.flags |= 32768, f !== null && typeof f == "object" && typeof f.then == "function") {
            var y = f, N = d, C = N.tag;
            if ((N.mode & 1) === 0 && (C === 0 || C === 11 || C === 15)) {
              var j = N.alternate;
              j ? (N.updateQueue = j.updateQueue, N.memoizedState = j.memoizedState, N.lanes = j.lanes) : (N.updateQueue = null, N.memoizedState = null);
            }
            var F = ra(s);
            if (F !== null) {
              F.flags &= -257, la(F, s, d, i, n), F.mode & 1 && ta(i, y, n), n = F, f = y;
              var W = n.updateQueue;
              if (W === null) {
                var D = /* @__PURE__ */ new Set();
                D.add(f), n.updateQueue = D;
              } else W.add(f);
              break e;
            } else {
              if ((n & 1) === 0) {
                ta(i, y, n), Mo();
                break e;
              }
              f = Error(c(426));
            }
          } else if (he && d.mode & 1) {
            var Ne = ra(s);
            if (Ne !== null) {
              (Ne.flags & 65536) === 0 && (Ne.flags |= 256), la(Ne, s, d, i, n), Xi(Mt(f, d));
              break e;
            }
          }
          i = f = Mt(f, d), Oe !== 4 && (Oe = 2), kr === null ? kr = [i] : kr.push(i), i = s;
          do {
            switch (i.tag) {
              case 3:
                i.flags |= 65536, n &= -n, i.lanes |= n;
                var m = ea(i, f, n);
                Ru(i, m);
                break e;
              case 1:
                d = f;
                var p = i.type, g = i.stateNode;
                if ((i.flags & 128) === 0 && (typeof p.getDerivedStateFromError == "function" || g !== null && typeof g.componentDidCatch == "function" && (Gn === null || !Gn.has(g)))) {
                  i.flags |= 65536, n &= -n, i.lanes |= n;
                  var L = na(i, d, n);
                  Ru(i, L);
                  break e;
                }
            }
            i = i.return;
          } while (i !== null);
        }
        Ia(t);
      } catch (V) {
        n = V, Ee === t && t !== null && (Ee = t = t.return);
        continue;
      }
      break;
    } while (!0);
  }
  function Fa() {
    var e = jl.current;
    return jl.current = gl, e === null ? gl : e;
  }
  function Mo() {
    (Oe === 0 || Oe === 3 || Oe === 2) && (Oe = 4), Ie === null || (at & 268435455) === 0 && (Nl & 268435455) === 0 || _n(Ie, qe);
  }
  function Tl(e, n) {
    var t = te;
    te |= 2;
    var r = Fa();
    (Ie !== e || qe !== n) && (In = null, dt(e, n));
    do
      try {
        _d();
        break;
      } catch (l) {
        Oa(e, l);
      }
    while (!0);
    if (Ji(), te = t, jl.current = r, Ee !== null) throw Error(c(261));
    return Ie = null, qe = 0, Oe;
  }
  function _d() {
    for (; Ee !== null; ) Ma(Ee);
  }
  function $d() {
    for (; Ee !== null && !Nc(); ) Ma(Ee);
  }
  function Ma(e) {
    var n = Va(e.alternate, e, sn);
    e.memoizedProps = e.pendingProps, n === null ? Ia(e) : Ee = n, Co.current = null;
  }
  function Ia(e) {
    var n = e;
    do {
      var t = n.alternate;
      if (e = n.return, (n.flags & 32768) === 0) {
        if (t = Zd(t, n, sn), t !== null) {
          Ee = t;
          return;
        }
      } else {
        if (t = Jd(t, n), t !== null) {
          t.flags &= 32767, Ee = t;
          return;
        }
        if (e !== null) e.flags |= 32768, e.subtreeFlags = 0, e.deletions = null;
        else {
          Oe = 6, Ee = null;
          return;
        }
      }
      if (n = n.sibling, n !== null) {
        Ee = n;
        return;
      }
      Ee = n = e;
    } while (n !== null);
    Oe === 0 && (Oe = 5);
  }
  function ft(e, n, t) {
    var r = ie, l = fn.transition;
    try {
      fn.transition = null, ie = 1, ef(e, n, t, r);
    } finally {
      fn.transition = l, ie = r;
    }
    return null;
  }
  function ef(e, n, t, r) {
    do
      Vt();
    while (Yn !== null);
    if ((te & 6) !== 0) throw Error(c(327));
    t = e.finishedWork;
    var l = e.finishedLanes;
    if (t === null) return null;
    if (e.finishedWork = null, e.finishedLanes = 0, t === e.current) throw Error(c(177));
    e.callbackNode = null, e.callbackPriority = 0;
    var i = t.lanes | t.childLanes;
    if (Mc(e, i), e === Ie && (Ee = Ie = null, qe = 0), (t.subtreeFlags & 2064) === 0 && (t.flags & 2064) === 0 || El || (El = !0, Ua(Mr, function() {
      return Vt(), null;
    })), i = (t.flags & 15990) !== 0, (t.subtreeFlags & 15990) !== 0 || i) {
      i = fn.transition, fn.transition = null;
      var s = ie;
      ie = 1;
      var d = te;
      te |= 4, Co.current = null, Qd(e, t), Ca(t, e), wd(Fi), Ar = !!Oi, Fi = Oi = null, e.current = t, Gd(t), Cc(), te = d, ie = s, fn.transition = i;
    } else e.current = t;
    if (El && (El = !1, Yn = e, Rl = l), i = e.pendingLanes, i === 0 && (Gn = null), zc(t.stateNode), $e(e, je()), n !== null) for (r = e.onRecoverableError, t = 0; t < n.length; t++) l = n[t], r(l.value, { componentStack: l.stack, digest: l.digest });
    if (Cl) throw Cl = !1, e = zo, zo = null, e;
    return (Rl & 1) !== 0 && e.tag !== 0 && Vt(), i = e.pendingLanes, (i & 1) !== 0 ? e === Po ? Sr++ : (Sr = 0, Po = e) : Sr = 0, Zn(), null;
  }
  function Vt() {
    if (Yn !== null) {
      var e = js(Rl), n = fn.transition, t = ie;
      try {
        if (fn.transition = null, ie = 16 > e ? 16 : e, Yn === null) var r = !1;
        else {
          if (e = Yn, Yn = null, Rl = 0, (te & 6) !== 0) throw Error(c(331));
          var l = te;
          for (te |= 4, I = e.current; I !== null; ) {
            var i = I, s = i.child;
            if ((I.flags & 16) !== 0) {
              var d = i.deletions;
              if (d !== null) {
                for (var f = 0; f < d.length; f++) {
                  var y = d[f];
                  for (I = y; I !== null; ) {
                    var N = I;
                    switch (N.tag) {
                      case 0:
                      case 11:
                      case 15:
                        xr(8, N, i);
                    }
                    var C = N.child;
                    if (C !== null) C.return = N, I = C;
                    else for (; I !== null; ) {
                      N = I;
                      var j = N.sibling, F = N.return;
                      if (wa(N), N === y) {
                        I = null;
                        break;
                      }
                      if (j !== null) {
                        j.return = F, I = j;
                        break;
                      }
                      I = F;
                    }
                  }
                }
                var W = i.alternate;
                if (W !== null) {
                  var D = W.child;
                  if (D !== null) {
                    W.child = null;
                    do {
                      var Ne = D.sibling;
                      D.sibling = null, D = Ne;
                    } while (D !== null);
                  }
                }
                I = i;
              }
            }
            if ((i.subtreeFlags & 2064) !== 0 && s !== null) s.return = i, I = s;
            else e: for (; I !== null; ) {
              if (i = I, (i.flags & 2048) !== 0) switch (i.tag) {
                case 0:
                case 11:
                case 15:
                  xr(9, i, i.return);
              }
              var m = i.sibling;
              if (m !== null) {
                m.return = i.return, I = m;
                break e;
              }
              I = i.return;
            }
          }
          var p = e.current;
          for (I = p; I !== null; ) {
            s = I;
            var g = s.child;
            if ((s.subtreeFlags & 2064) !== 0 && g !== null) g.return = s, I = g;
            else e: for (s = p; I !== null; ) {
              if (d = I, (d.flags & 2048) !== 0) try {
                switch (d.tag) {
                  case 0:
                  case 11:
                  case 15:
                    Sl(9, d);
                }
              } catch (V) {
                ke(d, d.return, V);
              }
              if (d === s) {
                I = null;
                break e;
              }
              var L = d.sibling;
              if (L !== null) {
                L.return = d.return, I = L;
                break e;
              }
              I = d.return;
            }
          }
          if (te = l, Zn(), Sn && typeof Sn.onPostCommitFiberRoot == "function") try {
            Sn.onPostCommitFiberRoot(Ir, e);
          } catch {
          }
          r = !0;
        }
        return r;
      } finally {
        ie = t, fn.transition = n;
      }
    }
    return !1;
  }
  function Wa(e, n, t) {
    n = Mt(t, n), n = ea(e, n, 1), e = Kn(e, n, 1), n = Qe(), e !== null && (Jt(e, 1, n), $e(e, n));
  }
  function ke(e, n, t) {
    if (e.tag === 3) Wa(e, e, t);
    else for (; n !== null; ) {
      if (n.tag === 3) {
        Wa(n, e, t);
        break;
      } else if (n.tag === 1) {
        var r = n.stateNode;
        if (typeof n.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (Gn === null || !Gn.has(r))) {
          e = Mt(t, e), e = na(n, e, 1), n = Kn(n, e, 1), e = Qe(), n !== null && (Jt(n, 1, e), $e(n, e));
          break;
        }
      }
      n = n.return;
    }
  }
  function nf(e, n, t) {
    var r = e.pingCache;
    r !== null && r.delete(n), n = Qe(), e.pingedLanes |= e.suspendedLanes & t, Ie === e && (qe & t) === t && (Oe === 4 || Oe === 3 && (qe & 130023424) === qe && 500 > je() - Ro ? dt(e, 0) : Eo |= t), $e(e, n);
  }
  function Da(e, n) {
    n === 0 && ((e.mode & 1) === 0 ? n = 1 : (n = Dr, Dr <<= 1, (Dr & 130023424) === 0 && (Dr = 4194304)));
    var t = Qe();
    e = On(e, n), e !== null && (Jt(e, n, t), $e(e, t));
  }
  function tf(e) {
    var n = e.memoizedState, t = 0;
    n !== null && (t = n.retryLane), Da(e, t);
  }
  function rf(e, n) {
    var t = 0;
    switch (e.tag) {
      case 13:
        var r = e.stateNode, l = e.memoizedState;
        l !== null && (t = l.retryLane);
        break;
      case 19:
        r = e.stateNode;
        break;
      default:
        throw Error(c(314));
    }
    r !== null && r.delete(n), Da(e, t);
  }
  var Va;
  Va = function(e, n, t) {
    if (e !== null) if (e.memoizedProps !== n.pendingProps || Ge.current) be = !0;
    else {
      if ((e.lanes & t) === 0 && (n.flags & 128) === 0) return be = !1, Xd(e, n, t);
      be = (e.flags & 131072) !== 0;
    }
    else be = !1, he && (n.flags & 1048576) !== 0 && gu(n, il, n.index);
    switch (n.lanes = 0, n.tag) {
      case 2:
        var r = n.type;
        wl(e, n), e = n.pendingProps;
        var l = Et(n, Be.current);
        Ot(n, t), l = ro(null, n, r, e, l, t);
        var i = lo();
        return n.flags |= 1, typeof l == "object" && l !== null && typeof l.render == "function" && l.$$typeof === void 0 ? (n.tag = 1, n.memoizedState = null, n.updateQueue = null, Ye(r) ? (i = !0, tl(n)) : i = !1, n.memoizedState = l.state !== null && l.state !== void 0 ? l.state : null, Yi(n), l.updater = yl, n.stateNode = l, l._reactInternals = n, co(n, r, e, t), n = mo(null, n, r, !0, i, t)) : (n.tag = 0, he && i && qi(n), Ke(null, n, l, t), n = n.child), n;
      case 16:
        r = n.elementType;
        e: {
          switch (wl(e, n), e = n.pendingProps, l = r._init, r = l(r._payload), n.type = r, l = n.tag = of(r), e = gn(r, e), l) {
            case 0:
              n = ho(null, n, r, e, t);
              break e;
            case 1:
              n = ca(null, n, r, e, t);
              break e;
            case 11:
              n = ia(null, n, r, e, t);
              break e;
            case 14:
              n = oa(null, n, r, gn(r.type, e), t);
              break e;
          }
          throw Error(c(
            306,
            r,
            ""
          ));
        }
        return n;
      case 0:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), ho(e, n, r, l, t);
      case 1:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), ca(e, n, r, l, t);
      case 3:
        e: {
          if (da(n), e === null) throw Error(c(387));
          r = n.pendingProps, i = n.memoizedState, l = i.element, Eu(e, n), dl(n, r, null, t);
          var s = n.memoizedState;
          if (r = s.element, i.isDehydrated) if (i = { element: r, isDehydrated: !1, cache: s.cache, pendingSuspenseBoundaries: s.pendingSuspenseBoundaries, transitions: s.transitions }, n.updateQueue.baseState = i, n.memoizedState = i, n.flags & 256) {
            l = Mt(Error(c(423)), n), n = fa(e, n, r, t, l);
            break e;
          } else if (r !== l) {
            l = Mt(Error(c(424)), n), n = fa(e, n, r, t, l);
            break e;
          } else for (on = Hn(n.stateNode.containerInfo.firstChild), ln = n, he = !0, vn = null, t = Nu(n, null, r, t), n.child = t; t; ) t.flags = t.flags & -3 | 4096, t = t.sibling;
          else {
            if (Pt(), r === l) {
              n = Mn(e, n, t);
              break e;
            }
            Ke(e, n, r, t);
          }
          n = n.child;
        }
        return n;
      case 5:
        return Pu(n), e === null && Bi(n), r = n.type, l = n.pendingProps, i = e !== null ? e.memoizedProps : null, s = l.children, Mi(r, l) ? s = null : i !== null && Mi(r, i) && (n.flags |= 32), aa(e, n), Ke(e, n, s, t), n.child;
      case 6:
        return e === null && Bi(n), null;
      case 13:
        return pa(e, n, t);
      case 4:
        return bi(n, n.stateNode.containerInfo), r = n.pendingProps, e === null ? n.child = Tt(n, null, r, t) : Ke(e, n, r, t), n.child;
      case 11:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), ia(e, n, r, l, t);
      case 7:
        return Ke(e, n, n.pendingProps, t), n.child;
      case 8:
        return Ke(e, n, n.pendingProps.children, t), n.child;
      case 12:
        return Ke(e, n, n.pendingProps.children, t), n.child;
      case 10:
        e: {
          if (r = n.type._context, l = n.pendingProps, i = n.memoizedProps, s = l.value, ae(ul, r._currentValue), r._currentValue = s, i !== null) if (mn(i.value, s)) {
            if (i.children === l.children && !Ge.current) {
              n = Mn(e, n, t);
              break e;
            }
          } else for (i = n.child, i !== null && (i.return = n); i !== null; ) {
            var d = i.dependencies;
            if (d !== null) {
              s = i.child;
              for (var f = d.firstContext; f !== null; ) {
                if (f.context === r) {
                  if (i.tag === 1) {
                    f = Fn(-1, t & -t), f.tag = 2;
                    var y = i.updateQueue;
                    if (y !== null) {
                      y = y.shared;
                      var N = y.pending;
                      N === null ? f.next = f : (f.next = N.next, N.next = f), y.pending = f;
                    }
                  }
                  i.lanes |= t, f = i.alternate, f !== null && (f.lanes |= t), Qi(
                    i.return,
                    t,
                    n
                  ), d.lanes |= t;
                  break;
                }
                f = f.next;
              }
            } else if (i.tag === 10) s = i.type === n.type ? null : i.child;
            else if (i.tag === 18) {
              if (s = i.return, s === null) throw Error(c(341));
              s.lanes |= t, d = s.alternate, d !== null && (d.lanes |= t), Qi(s, t, n), s = i.sibling;
            } else s = i.child;
            if (s !== null) s.return = i;
            else for (s = i; s !== null; ) {
              if (s === n) {
                s = null;
                break;
              }
              if (i = s.sibling, i !== null) {
                i.return = s.return, s = i;
                break;
              }
              s = s.return;
            }
            i = s;
          }
          Ke(e, n, l.children, t), n = n.child;
        }
        return n;
      case 9:
        return l = n.type, r = n.pendingProps.children, Ot(n, t), l = cn(l), r = r(l), n.flags |= 1, Ke(e, n, r, t), n.child;
      case 14:
        return r = n.type, l = gn(r, n.pendingProps), l = gn(r.type, l), oa(e, n, r, l, t);
      case 15:
        return sa(e, n, n.type, n.pendingProps, t);
      case 17:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), wl(e, n), n.tag = 1, Ye(r) ? (e = !0, tl(n)) : e = !1, Ot(n, t), _u(n, r, l), co(n, r, l, t), mo(null, n, r, !0, e, t);
      case 19:
        return ma(e, n, t);
      case 22:
        return ua(e, n, t);
    }
    throw Error(c(156, n.tag));
  };
  function Ua(e, n) {
    return ys(e, n);
  }
  function lf(e, n, t, r) {
    this.tag = e, this.key = t, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.ref = null, this.pendingProps = n, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
  }
  function pn(e, n, t, r) {
    return new lf(e, n, t, r);
  }
  function Io(e) {
    return e = e.prototype, !(!e || !e.isReactComponent);
  }
  function of(e) {
    if (typeof e == "function") return Io(e) ? 1 : 0;
    if (e != null) {
      if (e = e.$$typeof, e === ze) return 11;
      if (e === Pe) return 14;
    }
    return 2;
  }
  function $n(e, n) {
    var t = e.alternate;
    return t === null ? (t = pn(e.tag, n, e.key, e.mode), t.elementType = e.elementType, t.type = e.type, t.stateNode = e.stateNode, t.alternate = e, e.alternate = t) : (t.pendingProps = n, t.type = e.type, t.flags = 0, t.subtreeFlags = 0, t.deletions = null), t.flags = e.flags & 14680064, t.childLanes = e.childLanes, t.lanes = e.lanes, t.child = e.child, t.memoizedProps = e.memoizedProps, t.memoizedState = e.memoizedState, t.updateQueue = e.updateQueue, n = e.dependencies, t.dependencies = n === null ? null : { lanes: n.lanes, firstContext: n.firstContext }, t.sibling = e.sibling, t.index = e.index, t.ref = e.ref, t;
  }
  function Ll(e, n, t, r, l, i) {
    var s = 2;
    if (r = e, typeof e == "function") Io(e) && (s = 1);
    else if (typeof e == "string") s = 5;
    else e: switch (e) {
      case ge:
        return pt(t.children, l, i, n);
      case se:
        s = 8, l |= 8;
        break;
      case G:
        return e = pn(12, t, n, l | 2), e.elementType = G, e.lanes = i, e;
      case ne:
        return e = pn(13, t, n, l), e.elementType = ne, e.lanes = i, e;
      case we:
        return e = pn(19, t, n, l), e.elementType = we, e.lanes = i, e;
      case ue:
        return Ol(t, l, i, n);
      default:
        if (typeof e == "object" && e !== null) switch (e.$$typeof) {
          case Fe:
            s = 10;
            break e;
          case Ve:
            s = 9;
            break e;
          case ze:
            s = 11;
            break e;
          case Pe:
            s = 14;
            break e;
          case Te:
            s = 16, r = null;
            break e;
        }
        throw Error(c(130, e == null ? e : typeof e, ""));
    }
    return n = pn(s, t, n, l), n.elementType = e, n.type = r, n.lanes = i, n;
  }
  function pt(e, n, t, r) {
    return e = pn(7, e, r, n), e.lanes = t, e;
  }
  function Ol(e, n, t, r) {
    return e = pn(22, e, r, n), e.elementType = ue, e.lanes = t, e.stateNode = { isHidden: !1 }, e;
  }
  function Wo(e, n, t) {
    return e = pn(6, e, null, n), e.lanes = t, e;
  }
  function Do(e, n, t) {
    return n = pn(4, e.children !== null ? e.children : [], e.key, n), n.lanes = t, n.stateNode = { containerInfo: e.containerInfo, pendingChildren: null, implementation: e.implementation }, n;
  }
  function sf(e, n, t, r, l) {
    this.tag = n, this.containerInfo = e, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = ai(0), this.expirationTimes = ai(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = ai(0), this.identifierPrefix = r, this.onRecoverableError = l, this.mutableSourceEagerHydrationData = null;
  }
  function Vo(e, n, t, r, l, i, s, d, f) {
    return e = new sf(e, n, t, d, f), n === 1 ? (n = 1, i === !0 && (n |= 8)) : n = 0, i = pn(3, null, null, n), e.current = i, i.stateNode = e, i.memoizedState = { element: r, isDehydrated: t, cache: null, transitions: null, pendingSuspenseBoundaries: null }, Yi(i), e;
  }
  function uf(e, n, t) {
    var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
    return { $$typeof: Se, key: r == null ? null : "" + r, children: e, containerInfo: n, implementation: t };
  }
  function qa(e) {
    if (!e) return Xn;
    e = e._reactInternals;
    e: {
      if (nt(e) !== e || e.tag !== 1) throw Error(c(170));
      var n = e;
      do {
        switch (n.tag) {
          case 3:
            n = n.stateNode.context;
            break e;
          case 1:
            if (Ye(n.type)) {
              n = n.stateNode.__reactInternalMemoizedMergedChildContext;
              break e;
            }
        }
        n = n.return;
      } while (n !== null);
      throw Error(c(171));
    }
    if (e.tag === 1) {
      var t = e.type;
      if (Ye(t)) return hu(e, t, n);
    }
    return n;
  }
  function Aa(e, n, t, r, l, i, s, d, f) {
    return e = Vo(t, r, !0, e, l, i, s, d, f), e.context = qa(null), t = e.current, r = Qe(), l = bn(t), i = Fn(r, l), i.callback = n ?? null, Kn(t, i, l), e.current.lanes = l, Jt(e, l, r), $e(e, r), e;
  }
  function Fl(e, n, t, r) {
    var l = n.current, i = Qe(), s = bn(l);
    return t = qa(t), n.context === null ? n.context = t : n.pendingContext = t, n = Fn(i, s), n.payload = { element: e }, r = r === void 0 ? null : r, r !== null && (n.callback = r), e = Kn(l, n, s), e !== null && (wn(e, l, s, i), cl(e, l, s)), s;
  }
  function Ml(e) {
    if (e = e.current, !e.child) return null;
    switch (e.child.tag) {
      case 5:
        return e.child.stateNode;
      default:
        return e.child.stateNode;
    }
  }
  function Ha(e, n) {
    if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
      var t = e.retryLane;
      e.retryLane = t !== 0 && t < n ? t : n;
    }
  }
  function Uo(e, n) {
    Ha(e, n), (e = e.alternate) && Ha(e, n);
  }
  function af() {
    return null;
  }
  var Ba = typeof reportError == "function" ? reportError : function(e) {
    console.error(e);
  };
  function qo(e) {
    this._internalRoot = e;
  }
  Il.prototype.render = qo.prototype.render = function(e) {
    var n = this._internalRoot;
    if (n === null) throw Error(c(409));
    Fl(e, n, null, null);
  }, Il.prototype.unmount = qo.prototype.unmount = function() {
    var e = this._internalRoot;
    if (e !== null) {
      this._internalRoot = null;
      var n = e.containerInfo;
      ct(function() {
        Fl(null, e, null, null);
      }), n[zn] = null;
    }
  };
  function Il(e) {
    this._internalRoot = e;
  }
  Il.prototype.unstable_scheduleHydration = function(e) {
    if (e) {
      var n = Es();
      e = { blockedOn: null, target: e, priority: n };
      for (var t = 0; t < Un.length && n !== 0 && n < Un[t].priority; t++) ;
      Un.splice(t, 0, e), t === 0 && Ps(e);
    }
  };
  function Ao(e) {
    return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
  }
  function Wl(e) {
    return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11 && (e.nodeType !== 8 || e.nodeValue !== " react-mount-point-unstable "));
  }
  function Xa() {
  }
  function cf(e, n, t, r, l) {
    if (l) {
      if (typeof r == "function") {
        var i = r;
        r = function() {
          var y = Ml(s);
          i.call(y);
        };
      }
      var s = Aa(n, r, e, 0, null, !1, !1, "", Xa);
      return e._reactRootContainer = s, e[zn] = s.current, or(e.nodeType === 8 ? e.parentNode : e), ct(), s;
    }
    for (; l = e.lastChild; ) e.removeChild(l);
    if (typeof r == "function") {
      var d = r;
      r = function() {
        var y = Ml(f);
        d.call(y);
      };
    }
    var f = Vo(e, 0, !1, null, null, !1, !1, "", Xa);
    return e._reactRootContainer = f, e[zn] = f.current, or(e.nodeType === 8 ? e.parentNode : e), ct(function() {
      Fl(n, f, t, r);
    }), f;
  }
  function Dl(e, n, t, r, l) {
    var i = t._reactRootContainer;
    if (i) {
      var s = i;
      if (typeof l == "function") {
        var d = l;
        l = function() {
          var f = Ml(s);
          d.call(f);
        };
      }
      Fl(n, s, e, l);
    } else s = cf(t, n, e, l, r);
    return Ml(s);
  }
  Ns = function(e) {
    switch (e.tag) {
      case 3:
        var n = e.stateNode;
        if (n.current.memoizedState.isDehydrated) {
          var t = Zt(n.pendingLanes);
          t !== 0 && (ci(n, t | 1), $e(n, je()), (te & 6) === 0 && (Dt = je() + 500, Zn()));
        }
        break;
      case 13:
        ct(function() {
          var r = On(e, 1);
          if (r !== null) {
            var l = Qe();
            wn(r, e, 1, l);
          }
        }), Uo(e, 1);
    }
  }, di = function(e) {
    if (e.tag === 13) {
      var n = On(e, 134217728);
      if (n !== null) {
        var t = Qe();
        wn(n, e, 134217728, t);
      }
      Uo(e, 134217728);
    }
  }, Cs = function(e) {
    if (e.tag === 13) {
      var n = bn(e), t = On(e, n);
      if (t !== null) {
        var r = Qe();
        wn(t, e, n, r);
      }
      Uo(e, n);
    }
  }, Es = function() {
    return ie;
  }, Rs = function(e, n) {
    var t = ie;
    try {
      return ie = e, n();
    } finally {
      ie = t;
    }
  }, ri = function(e, n, t) {
    switch (n) {
      case "input":
        if (Gl(e, t), n = t.name, t.type === "radio" && n != null) {
          for (t = e; t.parentNode; ) t = t.parentNode;
          for (t = t.querySelectorAll("input[name=" + JSON.stringify("" + n) + '][type="radio"]'), n = 0; n < t.length; n++) {
            var r = t[n];
            if (r !== e && r.form === e.form) {
              var l = el(r);
              if (!l) throw Error(c(90));
              bo(r), Gl(r, l);
            }
          }
        }
        break;
      case "textarea":
        ts(e, t);
        break;
      case "select":
        n = t.value, n != null && ht(e, !!t.multiple, n, !1);
    }
  }, ds = Oo, fs = ct;
  var df = { usingClientEntryPoint: !1, Events: [ar, Nt, el, as, cs, Oo] }, jr = { findFiberByHostInstance: tt, bundleType: 0, version: "18.3.1", rendererPackageName: "react-dom" }, ff = { bundleType: jr.bundleType, version: jr.version, rendererPackageName: jr.rendererPackageName, rendererConfig: jr.rendererConfig, overrideHookState: null, overrideHookStateDeletePath: null, overrideHookStateRenamePath: null, overrideProps: null, overridePropsDeletePath: null, overridePropsRenamePath: null, setErrorHandler: null, setSuspenseHandler: null, scheduleUpdate: null, currentDispatcherRef: ve.ReactCurrentDispatcher, findHostInstanceByFiber: function(e) {
    return e = vs(e), e === null ? null : e.stateNode;
  }, findFiberByHostInstance: jr.findFiberByHostInstance || af, findHostInstancesForRefresh: null, scheduleRefresh: null, scheduleRoot: null, setRefreshHandler: null, getCurrentFiber: null, reconcilerVersion: "18.3.1-next-f1338f8080-20240426" };
  if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
    var Vl = __REACT_DEVTOOLS_GLOBAL_HOOK__;
    if (!Vl.isDisabled && Vl.supportsFiber) try {
      Ir = Vl.inject(ff), Sn = Vl;
    } catch {
    }
  }
  return en.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = df, en.createPortal = function(e, n) {
    var t = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
    if (!Ao(n)) throw Error(c(200));
    return uf(e, n, null, t);
  }, en.createRoot = function(e, n) {
    if (!Ao(e)) throw Error(c(299));
    var t = !1, r = "", l = Ba;
    return n != null && (n.unstable_strictMode === !0 && (t = !0), n.identifierPrefix !== void 0 && (r = n.identifierPrefix), n.onRecoverableError !== void 0 && (l = n.onRecoverableError)), n = Vo(e, 1, !1, null, null, t, !1, r, l), e[zn] = n.current, or(e.nodeType === 8 ? e.parentNode : e), new qo(n);
  }, en.findDOMNode = function(e) {
    if (e == null) return null;
    if (e.nodeType === 1) return e;
    var n = e._reactInternals;
    if (n === void 0)
      throw typeof e.render == "function" ? Error(c(188)) : (e = Object.keys(e).join(","), Error(c(268, e)));
    return e = vs(n), e = e === null ? null : e.stateNode, e;
  }, en.flushSync = function(e) {
    return ct(e);
  }, en.hydrate = function(e, n, t) {
    if (!Wl(n)) throw Error(c(200));
    return Dl(null, e, n, !0, t);
  }, en.hydrateRoot = function(e, n, t) {
    if (!Ao(e)) throw Error(c(405));
    var r = t != null && t.hydratedSources || null, l = !1, i = "", s = Ba;
    if (t != null && (t.unstable_strictMode === !0 && (l = !0), t.identifierPrefix !== void 0 && (i = t.identifierPrefix), t.onRecoverableError !== void 0 && (s = t.onRecoverableError)), n = Aa(n, null, e, 1, t ?? null, l, !1, i, s), e[zn] = n.current, or(e), r) for (e = 0; e < r.length; e++) t = r[e], l = t._getVersion, l = l(t._source), n.mutableSourceEagerHydrationData == null ? n.mutableSourceEagerHydrationData = [t, l] : n.mutableSourceEagerHydrationData.push(
      t,
      l
    );
    return new Il(n);
  }, en.render = function(e, n, t) {
    if (!Wl(n)) throw Error(c(200));
    return Dl(null, e, n, !1, t);
  }, en.unmountComponentAtNode = function(e) {
    if (!Wl(e)) throw Error(c(40));
    return e._reactRootContainer ? (ct(function() {
      Dl(null, null, e, !1, function() {
        e._reactRootContainer = null, e[zn] = null;
      });
    }), !0) : !1;
  }, en.unstable_batchedUpdates = Oo, en.unstable_renderSubtreeIntoContainer = function(e, n, t, r) {
    if (!Wl(t)) throw Error(c(200));
    if (e == null || e._reactInternals === void 0) throw Error(c(38));
    return Dl(e, n, t, !1, r);
  }, en.version = "18.3.1-next-f1338f8080-20240426", en;
}
var _a;
function wf() {
  if (_a) return Xo.exports;
  _a = 1;
  function u() {
    if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function"))
      try {
        __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(u);
      } catch (a) {
        console.error(a);
      }
  }
  return u(), Xo.exports = xf(), Xo.exports;
}
var $a;
function kf() {
  if ($a) return Ul;
  $a = 1;
  var u = wf();
  return Ul.createRoot = u.createRoot, Ul.hydrateRoot = u.hydrateRoot, Ul;
}
var Sf = kf();
const jf = "data:image/png;base64,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", ac = "" + new URL("owl_live-DzIuVESh.webp", import.meta.url).href, Nf = "" + new URL("NotoColorEmoji-nature-Rpfd13Si.woff2", import.meta.url).href, Cf = "" + new URL("NotoColorEmoji-objects-EKxheXEn.woff2", import.meta.url).href, Ef = { sans: 'Manrope, "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Avenir Next", "Segoe UI", sans-serif', mono: '"IBM Plex Mono", "SFMono-Regular", "SF Mono", Menlo, Consolas, monospace' }, Rf = { eyebrow: { size: "0.6875rem", weight: 650, lineHeight: "1.1", tracking: "0.12em" }, sectionLabel: { size: "0.6875rem", weight: 650, lineHeight: "1.1", tracking: "0.12em" }, pageTitle: { size: "1.375rem", weight: 650, lineHeight: "1.2", tracking: "-0.02em" }, subtitle: { size: "0.8125rem", weight: 450, lineHeight: "1.45", tracking: "0" }, body: { size: "0.9375rem", weight: 400, lineHeight: "1.6", tracking: "0" }, input: { size: "0.875rem", weight: 450, lineHeight: "1.5", tracking: "0" }, mono: { size: "0.75rem", weight: 600, lineHeight: "1.4", tracking: "0" }, scoreValue: { size: "1.25rem", weight: 600, lineHeight: "1", tracking: "-0.02em" }, scoreLabel: { size: "0.625rem", weight: 650, lineHeight: "1", tracking: "0.08em" }, footer: { size: "0.6875rem", weight: 450, lineHeight: "1.4", tracking: "0" } }, zf = { card: "12px", input: "10px", panel: "16px", pill: "999px" }, Pf = { duration: { fast: "120ms", mid: "200ms", slow: "420ms" }, easing: { standard: "cubic-bezier(.2, .8, .2, 1)", entrance: "cubic-bezier(.22, .8, .2, 1)" } }, Tf = { light: { washLow: "#FCEFD4", washHigh: "#F5B3A6", lineLow: "#E8A13C", lineHigh: "#D64540", safe: "#0E9384" }, dark: { washLow: "#4A3A1E", washHigh: "#4E2A26", lineLow: "#E0A24A", lineHigh: "#E8756B", safe: "#5FD6C6" } }, Lf = { light: { colorScheme: "light", canvas: "#FAF3F8", card: "#FFFFFF", surface: "rgba(255, 255, 255, 0.92)", surface2: "rgba(255, 255, 255, 0.80)", scrim: "radial-gradient(120% 90% at 50% 30%, rgba(250, 243, 248, 0.78), rgba(250, 243, 248, 0.30) 82%)", ink: "#231A21", muted: "#6B5F68", faint: "#A395A0", line: "#F0DFEA", lineStrong: "#E2C8D8", brand: "#E562A8", brandBright: "#EF7CB8", brandWash: "#FBE7F2", safe: "#0E9384", safeWash: "#D7F0EB", warning: "#81520C", warningWash: "#FCEFD4", riskInk: "#D64540", riskWash: "#F8DDD7", focus: "#1B6ED1", link: "#0E9384", mint: "#AFDEDD", shadowColor: "rgba(65, 45, 61, 0.14)", shadowCard: "0 1px 2px rgba(16, 24, 40, 0.04)", shadowRaised: "0 22px 62px rgba(69, 37, 57, 0.12)", sidebarBg: "rgba(255, 255, 255, 0.92)", inputBg: "rgba(255, 255, 255, 0.96)", popoverBg: "rgba(255, 255, 255, 0.98)", optionHover: "rgba(229, 98, 168, 0.16)", btnBg: "rgba(229, 98, 168, 0.10)", btnHoverBg: "rgba(229, 98, 168, 0.20)", btnHoverBorder: "rgba(229, 98, 168, 0.50)", pillBg: "rgba(255, 255, 255, 0.70)", pillSelected: "linear-gradient(135deg, rgba(229, 98, 168, 0.22), rgba(14, 147, 132, 0.16))", pillSelectedBorder: "rgba(229, 98, 168, 0.55)", scrollThumb: "rgba(229, 98, 168, 0.50)", scrollThumb2: "rgba(229, 98, 168, 0.42)", scrollThumbHover: "rgba(229, 98, 168, 0.66)" }, dark: { colorScheme: "dark", canvas: "#151116", card: "#211A22", surface: "rgba(33, 26, 34, 0.92)", surface2: "rgba(33, 26, 34, 0.80)", scrim: "radial-gradient(120% 90% at 50% 30%, rgba(18, 13, 20, 0.50), rgba(18, 13, 20, 0.10) 82%)", ink: "#F9F5F7", muted: "#B9ADB5", faint: "#8E8089", line: "rgba(255, 231, 242, 0.15)", lineStrong: "rgba(255, 231, 242, 0.26)", brand: "#F07EBB", brandBright: "#F79BCB", brandWash: "#4D2034", safe: "#5FD6C6", safeWash: "#173B37", warning: "#F0BE6D", warningWash: "#422F17", riskInk: "#FF9499", riskWash: "#4E2428", focus: "#6CAEFF", link: "#7FD8CA", mint: "#AFDEDD", shadowColor: "rgba(0, 0, 0, 0.50)", shadowCard: "0 1px 2px rgba(0, 0, 0, 0.30)", shadowRaised: "0 24px 70px rgba(0, 0, 0, 0.32)", sidebarBg: "rgba(21, 17, 22, 0.93)", inputBg: "rgba(20, 16, 24, 0.80)", popoverBg: "rgba(24, 18, 28, 0.97)", optionHover: "rgba(240, 126, 187, 0.22)", btnBg: "rgba(240, 126, 187, 0.16)", btnHoverBg: "rgba(240, 126, 187, 0.28)", btnHoverBorder: "rgba(240, 126, 187, 0.55)", pillBg: "rgba(33, 26, 34, 0.66)", pillSelected: "linear-gradient(135deg, rgba(240, 126, 187, 0.30), rgba(95, 214, 198, 0.20))", pillSelectedBorder: "rgba(240, 126, 187, 0.60)", scrollThumb: "rgba(240, 126, 187, 0.50)", scrollThumb2: "rgba(240, 126, 187, 0.42)", scrollThumbHover: "rgba(240, 126, 187, 0.66)" } }, nn = {
  fonts: Ef,
  type: Rf,
  radii: zf,
  motion: Pf,
  spanRamp: Tf,
  palette: Lf
};
function ec(u) {
  const a = nn.palette[u], c = nn.spanRamp[u];
  return {
    "--canvas": a.canvas,
    "--surface": a.surface,
    "--surface-solid": a.card,
    "--ink": a.ink,
    "--muted": a.muted,
    "--faint": a.faint,
    "--line": a.line,
    "--line-strong": a.lineStrong,
    "--brand": a.brand,
    "--brand-bright": a.brandBright,
    "--brand-wash": a.brandWash,
    "--safe": a.safe,
    "--safe-wash": a.safeWash,
    "--warning": a.warning,
    "--warning-wash": a.warningWash,
    "--risk-ink": a.riskInk,
    "--risk-wash": a.riskWash,
    "--focus": a.focus,
    "--shadow": a.shadowRaised,
    "--shadow-whisper": a.shadowCard,
    "--span-wash-low": c.washLow,
    "--span-wash-high": c.washHigh,
    "--span-line-low": c.lineLow,
    "--span-line-high": c.lineHigh,
    "--span-safe": c.safe
  };
}
function Of() {
  const u = {};
  for (const [a, c] of Object.entries(nn.type))
    u[`--text-${a}-size`] = c.size, u[`--text-${a}-weight`] = String(c.weight), u[`--text-${a}-line`] = c.lineHeight, u[`--text-${a}-tracking`] = c.tracking;
  return u;
}
function Ff() {
  return {
    "--font-sans": nn.fonts.sans,
    "--font-mono": nn.fonts.mono,
    "--radius-card": nn.radii.card,
    "--radius-input": nn.radii.input,
    "--radius-panel": nn.radii.panel,
    "--radius-pill": nn.radii.pill,
    "--dur-fast": nn.motion.duration.fast,
    "--dur-mid": nn.motion.duration.mid,
    "--dur-slow": nn.motion.duration.slow,
    "--ease-standard": nn.motion.easing.standard,
    "--ease-entrance": nn.motion.easing.entrance,
    ...Of()
  };
}
function nc(u, a) {
  const c = Object.entries(a).map(([x, w]) => `  ${x}: ${w};`).join(`
`);
  return `${u} {
${c}
}`;
}
const Mf = [
  nc(".sirin-component-root", { ...Ff(), ...ec("light") }),
  nc(".sirin-workspace[data-theme='dark']", ec("dark"))
].join(`

`), cc = "recordedResultVerified", If = {
  recordedResultVerified: "Recorded result · verified — detection not live"
};
let tc = !1;
function Wf(u) {
  if (u.querySelector(":scope > style[data-sirin-tokens]")) return;
  const a = document.createElement("style");
  a.setAttribute("data-sirin-tokens", ""), a.textContent = Mf, u.prepend(a);
}
function Df() {
  if (tc || typeof FontFace > "u") return;
  tc = !0;
  const u = [
    new FontFace("Noto Color Emoji", `url(${Cf})`, { style: "normal", weight: "400", unicodeRange: "U+1F9EA" }),
    new FontFace("Noto Color Emoji", `url(${Nf})`, { style: "normal", weight: "400", unicodeRange: "U+1F984" })
  ];
  for (const a of u)
    document.fonts.add(a), a.load().catch(() => document.fonts.delete(a));
}
function Jl() {
  var u;
  return ((u = globalThis.matchMedia) == null ? void 0 : u.call(globalThis, "(prefers-reduced-motion: reduce)").matches) ?? !1;
}
const rc = {
  analyze: {
    task: "faithfulness",
    mode: "generate",
    exampleId: null,
    context: "",
    question: "",
    answer: "",
    prompt: "",
    sourceRunId: null
  }
}, Vf = { theme: "light", motion: "subtle" }, dc = 240, fc = 180, Uf = 400, lc = /* @__PURE__ */ new Set(), qf = /* @__PURE__ */ new Set(["consent_required", "busy", "empty_answer", "generation_unavailable", "judge_no_aligned_annotation", "provider_rate_limited", "provider_auth_failed"]), ql = /* @__PURE__ */ new Map();
function Af(u) {
  return u ? { analyze: { ...rc.analyze, ...u.analyze, prompt: u.analyze.prompt ?? "", sourceRunId: u.analyze.sourceRunId ?? null }, quickPrompt: u.quickPrompt ?? "" } : { analyze: { ...rc.analyze }, quickPrompt: "" };
}
function ic() {
  var c, x, w, v;
  const u = (c = globalThis.sessionStorage) == null ? void 0 : c.getItem("sirin.client.id");
  if (u) return u;
  const a = ((w = (x = globalThis.crypto) == null ? void 0 : x.randomUUID) == null ? void 0 : w.call(x)) ?? `client-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return (v = globalThis.sessionStorage) == null || v.setItem("sirin.client.id", a), a;
}
function oc() {
  var u, a;
  return ((a = (u = globalThis.crypto) == null ? void 0 : u.randomUUID) == null ? void 0 : a.call(u)) ?? `action-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
function Ae(u, a = !0) {
  return typeof u == "boolean" ? u : u && typeof u == "object" ? u.enabled : a;
}
function sc(u) {
  return u && typeof u == "object" ? u.reason ?? void 0 : void 0;
}
function Rn(u) {
  return u ? u.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (a) => a.toUpperCase()) : "Unavailable";
}
function Ko(u) {
  return u === "faithfulness" ? "Hallucination" : Rn(u);
}
function De(u) {
  return typeof u == "number" && Number.isFinite(u) ? u : null;
}
function Go(u) {
  return Math.min(1, Math.max(0, u));
}
function pc(u) {
  return u >= 0.995 ? "1.0" : u.toFixed(2).replace(/^0+/, "");
}
function zr(u, a, c) {
  return `color-mix(in srgb, var(${a}) ${Math.round(Go(c) * 100)}%, var(${u}))`;
}
function Bl(u, a, c) {
  return a === !0 || u !== null && c !== null && u >= c;
}
function hc(u, a) {
  const c = a ?? 0;
  return Go((u - c) / Math.max(1 - c, 1e-6));
}
function Er(u, a) {
  const c = De(u);
  return c === null ? "No score" : ["calibrated_probability", "calibratedProbability", "categorical_probabilities", "categoricalProbabilities"].includes(a ?? "") ? `${Math.round(c * 100)}%` : c.toFixed(c < 10 ? 2 : 1);
}
function Yo(u, a) {
  const c = a == null ? void 0 : a.trim();
  return c || (["calibrated_probability", "calibratedProbability"].includes(u ?? "") ? "calibrated probability" : ["relative_within_answer", "relativeWithinAnswer"].includes(u ?? "") ? "relative within this answer — not comparable across runs" : ["thresholded_raw_score", "thresholdedRawScore"].includes(u ?? "") ? "raw score vs decision threshold τ" : ["categorical_probabilities", "categoricalProbabilities"].includes(u ?? "") ? "class confidence" : ["span_agreement", "spanAgreement"].includes(u ?? "") ? "judge agreement" : u === "verdict" ? "verdict" : null);
}
function Kl(u) {
  if (typeof u != "string") return "neutral";
  const a = u.trim().toLowerCase().replaceAll("_", " ").replaceAll("-", " ");
  return ["risk", "suspect", "unsupported", "hallucinated", "hallucination", "failed", "error", "unanswerable", "unsafe"].includes(a) ? "risk" : ["safe", "supported", "faithful", "answerable", "passed", "grounded", "healthy"].includes(a) ? "safe" : "neutral";
}
function Al(u, a, c) {
  const x = (u == null ? void 0 : u[a]) ?? (u == null ? void 0 : u[c]);
  return x == null || x === "" ? "Not configured" : String(x);
}
function mc({ status: u }) {
  return /* @__PURE__ */ o.jsx("span", { className: `status-dot ${Kl(u)}`, "aria-hidden": "true" });
}
function He({ name: u }) {
  const a = {
    analyze: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M4 17.5 9 12l3 3 7-8" }),
      /* @__PURE__ */ o.jsx("path", { d: "M15 7h4v4" })
    ] }),
    runs: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M6 5h12M6 12h12M6 19h12" }),
      /* @__PURE__ */ o.jsx("path", { d: "M3 5h.01M3 12h.01M3 19h.01" })
    ] }),
    diagnostics: /* @__PURE__ */ o.jsx(o.Fragment, { children: /* @__PURE__ */ o.jsx("path", { d: "M4 14h3l2-7 4 11 2-7h5" }) }),
    arrow: /* @__PURE__ */ o.jsx(o.Fragment, { children: /* @__PURE__ */ o.jsx("path", { d: "m9 18 6-6-6-6" }) }),
    spark: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6Z" }),
      /* @__PURE__ */ o.jsx("path", { d: "m18 15 .7 2.3L21 18l-2.3.7L18 21l-.7-2.3L15 18l2.3-.7Z" })
    ] }),
    download: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M12 3v12m-5-5 5 5 5-5" }),
      /* @__PURE__ */ o.jsx("path", { d: "M5 21h14" })
    ] }),
    upload: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M12 21V9m-5 5 5-5 5 5" }),
      /* @__PURE__ */ o.jsx("path", { d: "M5 3h14" })
    ] })
  };
  return /* @__PURE__ */ o.jsx("svg", { className: "icon", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: a[u] });
}
function Hf({
  workspace: u,
  onWorkspace: a,
  setup: c,
  title: x,
  subtitle: w,
  busy: v,
  motion: E
}) {
  const [R, T] = le.useState(!1), k = le.useId(), U = E === "lively" && v && !Jl();
  return le.useEffect(() => {
    if (!R) return;
    const q = (X) => {
      X.key === "Escape" && T(!1);
    };
    return globalThis.addEventListener("keydown", q), () => globalThis.removeEventListener("keydown", q);
  }, [R]), /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
    /* @__PURE__ */ o.jsxs("header", { className: "shell-header", children: [
      /* @__PURE__ */ o.jsxs("button", { className: "brand", type: "button", onClick: () => a("analyze"), "aria-label": "SIRIN Analyze home", children: [
        /* @__PURE__ */ o.jsx("img", { src: U ? ac : jf, alt: "" }),
        /* @__PURE__ */ o.jsxs("span", { children: [
          /* @__PURE__ */ o.jsx("b", { children: "SIRIN" }),
          /* @__PURE__ */ o.jsx("small", { children: "Honesty, made visible." })
        ] })
      ] }),
      /* @__PURE__ */ o.jsx("nav", { className: "workspace-tabs", "aria-label": "Workspace", children: ["analyze", "runs", "diagnostics"].map((q) => /* @__PURE__ */ o.jsxs("button", { type: "button", "data-workspace-tab": q, className: u === q ? "active" : "", "aria-current": u === q ? "page" : void 0, onClick: () => a(q), children: [
        /* @__PURE__ */ o.jsx(He, { name: q }),
        Rn(q)
      ] }, q)) }),
      /* @__PURE__ */ o.jsxs("button", { className: "setup-chip", type: "button", onClick: () => T((q) => !q), "aria-expanded": R, "aria-controls": k, children: [
        /* @__PURE__ */ o.jsxs("span", { className: "setup-summary", children: [
          /* @__PURE__ */ o.jsx("small", { children: "Detector" }),
          /* @__PURE__ */ o.jsx("b", { children: Al(c, "detectorPreset", "detectorLabel") })
        ] }),
        /* @__PURE__ */ o.jsx(He, { name: "arrow" })
      ] })
    ] }),
    R && /* @__PURE__ */ o.jsxs("div", { className: "setup-popover", id: k, role: "region", "aria-label": "Active setup", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Active setup" }),
      /* @__PURE__ */ o.jsxs("dl", { children: [
        /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Detector" }),
          /* @__PURE__ */ o.jsx("dd", { children: Al(c, "detectorPreset", "detectorLabel") })
        ] }),
        /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Generator" }),
          /* @__PURE__ */ o.jsx("dd", { children: (c == null ? void 0 : c.providerLabel) ?? (c == null ? void 0 : c.modelId) ?? Al(c, "modelLabel", "model") })
        ] }),
        /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Device" }),
          /* @__PURE__ */ o.jsx("dd", { children: (c == null ? void 0 : c.device) ?? "Automatic" })
        ] }),
        (c == null ? void 0 : c.layer) !== void 0 && c.layer !== null && /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Layer" }),
          /* @__PURE__ */ o.jsx("dd", { children: c.layer })
        ] }),
        (c == null ? void 0 : c.threshold) !== void 0 && c.threshold !== null && /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Threshold" }),
          /* @__PURE__ */ o.jsx("dd", { children: c.threshold })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ o.jsxs("section", { className: "page-head", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: u === "analyze" ? "Evidence workspace" : Rn(u) }),
      /* @__PURE__ */ o.jsx("h1", { children: x ?? (u === "analyze" ? "See where an answer leaves the evidence." : u === "runs" ? "Every result, with its receipts." : u === "compare" ? "Two detectors, one answer, side by side." : "Know what SIRIN is running.") }),
      /* @__PURE__ */ o.jsx("p", { children: w ?? (u === "analyze" ? "Generate or supply an answer. SIRIN checks it against context and makes uncertainty legible." : u === "runs" ? "Review immutable outcomes and carry portable records between sessions." : u === "compare" ? "Both detectors score the same answer. Localization overlap is comparable; scores are only compared when their scales are." : "Inspect the active runtime without exposing sensitive internals.") })
    ] })
  ] });
}
function kn({ label: u, hint: a, children: c }) {
  return /* @__PURE__ */ o.jsxs("label", { className: "field", children: [
    /* @__PURE__ */ o.jsxs("span", { children: [
      u,
      a && /* @__PURE__ */ o.jsx("small", { children: a })
    ] }),
    c
  ] });
}
function Hl({ value: u, onChange: a, ariaLabel: c, children: x }) {
  return /* @__PURE__ */ o.jsxs("span", { className: "select-wrap", children: [
    /* @__PURE__ */ o.jsx("select", { value: u, "aria-label": c, onChange: a, children: x }),
    /* @__PURE__ */ o.jsx("svg", { className: "select-chevron", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: /* @__PURE__ */ o.jsx("path", { d: "m6 9 6 6 6-6" }) })
  ] });
}
function Bf({ examples: u, selected: a, hosted: c, onSelect: x, onCustom: w }) {
  return u.length ? /* @__PURE__ */ o.jsxs("div", { className: "examples", children: [
    /* @__PURE__ */ o.jsx("span", { children: "Try an example" }),
    /* @__PURE__ */ o.jsxs("div", { className: "example-list", children: [
      c && /* @__PURE__ */ o.jsxs("button", { type: "button", className: a === null ? "selected" : "", title: "Enter your own context and question, then generate and score a live answer.", onClick: w, children: [
        /* @__PURE__ */ o.jsx("span", { className: "example-label", children: "Custom" }),
        /* @__PURE__ */ o.jsx("span", { className: "example-source", children: "your own input" })
      ] }, "__custom__"),
      u.map((v) => {
        var R, T;
        const E = (T = (R = v.provenance) == null ? void 0 : R.sourceModel) == null ? void 0 : T.split("/").pop();
        return /* @__PURE__ */ o.jsxs("button", { type: "button", disabled: !!v.disabledReason, title: v.disabledReason ?? v.description, className: a === v.id ? "selected" : "", onClick: () => x(v), children: [
          /* @__PURE__ */ o.jsx("span", { className: "example-label", children: v.label }),
          E && /* @__PURE__ */ o.jsxs("span", { className: "example-source", children: [
            "answer by ",
            E
          ] })
        ] }, v.id);
      })
    ] })
  ] }) : null;
}
function Xf(u, a) {
  const c = u == null ? void 0 : u.status, x = u != null && u.runId ? a.find((v) => v.id === u.runId) : void 0, w = `${(x == null ? void 0 : x.origin) ?? ""} ${(x == null ? void 0 : x.mode) ?? ""} ${(x == null ? void 0 : x.task) ?? ""}`;
  return c === "running" ? /answerability/i.test(w) ? { label: "Checking answerability…", detail: "Judging whether the question is answerable from the context." } : /generat|quickPrompt/i.test(w) ? { label: "Generating…", detail: "The model is drafting an answer, then SIRIN scores it against the context." } : { label: "Scoring…", detail: "Running the detector over the answer." } : c === "queued" ? { label: "Queued…", detail: "Waiting for the runtime to pick up this run." } : { label: "Working…", detail: "The result will appear here when the operation finishes." };
}
function Xl({ activity: u, runs: a = [] }) {
  const { label: c, detail: x } = Xf(u, a);
  return /* @__PURE__ */ o.jsxs("section", { className: "result-card activity-card", "aria-live": "polite", "aria-busy": "true", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "activity-status", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Working" }),
      /* @__PURE__ */ o.jsx("h2", { children: c }),
      /* @__PURE__ */ o.jsx("p", { children: x })
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "skeleton-lines", "aria-hidden": "true", children: [
      /* @__PURE__ */ o.jsx("i", {}),
      /* @__PURE__ */ o.jsx("i", {}),
      /* @__PURE__ */ o.jsx("i", {}),
      /* @__PURE__ */ o.jsx("i", {})
    ] })
  ] });
}
function Zf({ answer: u, motion: a }) {
  const c = a !== "static" && !Jl();
  return /* @__PURE__ */ o.jsxs("section", { className: "result-card activity-card", "aria-live": "polite", "aria-busy": "true", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "activity-status", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Scoring…" }),
      /* @__PURE__ */ o.jsx("h2", { children: "Replaying the recorded answer" }),
      /* @__PURE__ */ o.jsx("p", { children: "The judge is scoring this answer against the context; graded evidence appears when it finishes." })
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "answer-block", children: [
      /* @__PURE__ */ o.jsx("div", { className: "answer-label", children: /* @__PURE__ */ o.jsx("span", { children: "Answer" }) }),
      c ? /* @__PURE__ */ o.jsx(vc, { answer: u, onComplete: () => {
      } }) : /* @__PURE__ */ o.jsx("p", { className: "answer-copy", children: u })
    ] })
  ] });
}
function vc({ answer: u, onComplete: a }) {
  const c = le.useRef(a);
  c.current = a;
  const [x, w] = le.useState("");
  return le.useEffect(() => {
    w("");
    const v = u.match(/\S+\s*/g) ?? [u];
    let E = 0;
    const R = globalThis.setInterval(() => {
      E += 1, w(v.slice(0, E).join("")), E >= v.length && (globalThis.clearInterval(R), c.current());
    }, Math.max(24, Math.min(70, 900 / Math.max(v.length, 1))));
    return () => globalThis.clearInterval(R);
  }, [u]), /* @__PURE__ */ o.jsxs("p", { className: "answer-copy", children: [
    x,
    /* @__PURE__ */ o.jsx("span", { className: x.length < u.length ? "caret" : "caret hidden", "aria-hidden": "true" })
  ] });
}
function Jf({ answer: u, result: a }) {
  var E;
  if (!((E = a.segments) != null && E.length)) return /* @__PURE__ */ o.jsx("p", { className: "answer-copy", children: u || "No answer was returned." });
  const c = De(a.threshold), x = a.segments.map((R) => {
    const T = De(R.score);
    return Bl(T, R.verdict, c) ? T ?? 1 : -1;
  }), w = x.indexOf(Math.max(...x));
  let v = 0;
  return /* @__PURE__ */ o.jsx("p", { className: "answer-copy segmented", children: a.segments.map((R, T) => {
    const k = De(R.score), U = Bl(k, R.verdict, c), q = R.startCodePoint !== void 0 ? `characters ${R.startCodePoint}–${R.endCodePoint}` : "text segment", X = [q, k !== null ? `score ${k.toFixed(2)}` : null, c !== null ? `τ ${c.toFixed(3)}` : null, "probe confidence, not calibrated"].filter(Boolean).join(" · ");
    if (U) {
      const oe = k !== null ? hc(k, c) : 1, me = zr("--span-line-low", "--span-line-high", oe), K = { "--seg-wash": zr("--span-wash-low", "--span-wash-high", oe), "--seg-line": me, borderBottomWidth: oe >= 0.5 ? "3px" : "2px", "--d": `${dc + v * fc}ms` }, Z = T === w ? "evidence graded is-peak" : "evidence graded";
      return v += 1, /* @__PURE__ */ o.jsxs("span", { className: Z, style: K, tabIndex: 0, "aria-label": `${R.text}, ${X}`, title: X, children: [
        R.text,
        k !== null && /* @__PURE__ */ o.jsx("sup", { className: "evidence-badge", children: pc(k) })
      ] }, `${q}-${T}`);
    }
    return k !== null ? /* @__PURE__ */ o.jsx("span", { className: "evidence below", title: X, children: R.text }, `${q}-${T}`) : /* @__PURE__ */ o.jsx("span", { className: "evidence", children: R.text }, `${q}-${T}`);
  }) });
}
function Kf({ chunks: u, semantics: a }) {
  if (!u || u.length < 2) return null;
  const c = u.map((E) => De(E.score)).filter((E) => E !== null);
  if (!c.length) return null;
  const x = Math.min(...c), w = Math.max(...c) - x, v = Yo(a) ?? "relative within this answer";
  return /* @__PURE__ */ o.jsxs("div", { className: "context-heatbar", role: "group", "aria-label": "Per-chunk context scores", children: [
    /* @__PURE__ */ o.jsx("span", { className: "context-heatbar-title", children: "Context chunks" }),
    /* @__PURE__ */ o.jsx("div", { className: "context-heatbar-cells", children: u.map((E, R) => {
      const T = De(E.score), k = T === null || w <= 0 ? 0.5 : Go((T - x) / w), U = `Chunk ${(De(E.index) ?? R) + 1} of ${u.length}${T !== null ? ` · score ${T.toFixed(2)}` : ""} · ${v}`;
      return /* @__PURE__ */ o.jsx("span", { className: "context-heatbar-cell", style: { "--seg-wash": zr("--span-wash-low", "--span-wash-high", k), "--seg-line": zr("--span-line-low", "--span-line-high", k) }, tabIndex: 0, title: U, "aria-label": U }, R);
    }) })
  ] });
}
function Qf({ result: u }) {
  const a = De(u.threshold), c = (u.segments ?? []).filter((R) => Bl(De(R.score), R.verdict, a)), x = c.map((R) => De(R.score)).filter((R) => R !== null), w = x.length ? Math.max(...x) : null, v = c.length ? zr("--span-line-low", "--span-line-high", w !== null ? hc(w, a) : 1) : "var(--span-safe)", E = c.length ? `${c.length} suspect ${c.length === 1 ? "span" : "spans"}${w !== null ? ` · max risk ${w.toFixed(2)}` : ""}` : "No spans above threshold";
  return /* @__PURE__ */ o.jsxs("div", { className: "span-footer", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "span-verdict", children: [
      /* @__PURE__ */ o.jsx("span", { className: "span-verdict-dot", style: { background: v }, "aria-hidden": "true" }),
      E
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "span-legend", children: [
      /* @__PURE__ */ o.jsx("span", { className: "span-legend-word", children: "risk" }),
      a !== null && /* @__PURE__ */ o.jsxs("span", { className: "span-legend-num", children: [
        "τ ",
        a.toFixed(2)
      ] }),
      /* @__PURE__ */ o.jsx("span", { className: "span-legend-bar", "aria-hidden": "true" }),
      /* @__PURE__ */ o.jsx("span", { className: "span-legend-num", children: "1.00" })
    ] })
  ] });
}
function Gf({ result: u }) {
  var w, v, E, R, T;
  const a = (w = u.spans) != null && w.length ? u.spans : (u.segments ?? []).filter((k) => k.verdict === !0).map((k) => ({ text: k.text, startCodePoint: k.startCodePoint, endCodePoint: k.endCodePoint, score: k.score, scoreKind: u.scoreSemantics, verdict: "suspect" })), c = u.categories ?? (Array.isArray(u.classes) ? u.classes : Object.entries(u.classes ?? {}).map(([k, U]) => ({ label: k, score: U })));
  return !(a.length || (v = u.claims) != null && v.length || c.length || u.rationale || u.note || (E = u.values) != null && E.length) ? null : /* @__PURE__ */ o.jsxs("details", { className: "evidence-details", children: [
    /* @__PURE__ */ o.jsx("summary", { children: "Evidence details" }),
    a.length ? /* @__PURE__ */ o.jsx("div", { className: "evidence-list", "aria-label": "Suspect spans", children: a.map((k, U) => /* @__PURE__ */ o.jsxs("article", { children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("b", { children: k.text }),
        /* @__PURE__ */ o.jsx("small", { children: k.startCodePoint !== void 0 ? `Characters ${k.startCodePoint}–${k.endCodePoint}` : "Span evidence" })
      ] }),
      /* @__PURE__ */ o.jsxs("span", { children: [
        De(k.score) !== null ? pc(De(k.score)) : Er(k.score, k.scoreKind),
        " · ",
        k.verdict ?? "scored"
      ] })
    ] }, `${k.startCodePoint}-${U}`)) }) : null,
    (R = u.claims) != null && R.length ? /* @__PURE__ */ o.jsx("div", { className: "claim-list", children: u.claims.map((k, U) => /* @__PURE__ */ o.jsxs("article", { className: Kl(k.verdict), children: [
      /* @__PURE__ */ o.jsx(mc, { status: k.supported === !0 ? "safe" : k.supported === !1 ? "risk" : k.verdict }),
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("b", { children: k.text ?? k.claim ?? `Claim ${U + 1}` }),
        k.rationale && /* @__PURE__ */ o.jsx("p", { children: k.rationale })
      ] }),
      /* @__PURE__ */ o.jsx("span", { children: k.verdict ?? Er(k.score) })
    ] }, U)) }) : null,
    c.length ? /* @__PURE__ */ o.jsx("div", { className: "class-list", "aria-label": "Class scores", children: c.map((k, U) => /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("span", { children: Rn(k.label) }),
      /* @__PURE__ */ o.jsx("i", { children: /* @__PURE__ */ o.jsx("b", { style: { width: `${Math.max(0, Math.min(100, k.score * 100))}%` } }) }),
      /* @__PURE__ */ o.jsx("strong", { children: Er(k.score, "categorical_probabilities") })
    ] }, `${k.label}-${U}`)) }) : null,
    (T = u.values) != null && T.length ? /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("div", { className: "mini-bars", "aria-hidden": "true", children: u.values.map((k, U) => /* @__PURE__ */ o.jsx("i", { style: { height: `${10 + Math.max(0, Math.min(1, k)) * 54}px` } }, U)) }),
      /* @__PURE__ */ o.jsx("ol", { className: "sr-only", "aria-label": "Relative token scores", children: u.values.map((k, U) => /* @__PURE__ */ o.jsxs("li", { children: [
        "Item ",
        U + 1,
        ": ",
        k.toFixed(3)
      ] }, U)) })
    ] }) : null,
    (u.rationale || u.note) && /* @__PURE__ */ o.jsx("p", { className: "rationale", children: u.rationale ?? u.note })
  ] });
}
function Yf({ run: u }) {
  const a = u.provenance ?? {}, c = u.origin === cc, x = !c && /replay|recorded/i.test(`${u.origin ?? ""} ${u.mode ?? ""}`), w = c && typeof a.integritySha256 == "string" ? a.integritySha256 : null, v = Object.entries(a).filter(([E, R]) => E !== (w ? "integritySha256" : "") && (typeof R == "string" || typeof R == "number" || typeof R == "boolean"));
  return /* @__PURE__ */ o.jsxs("div", { className: "provenance", children: [
    /* @__PURE__ */ o.jsx("span", { children: c ? "Recorded result · verified" : Rn(u.origin ?? u.mode ?? "live run") }),
    (u.setupSnapshot ?? u.setup) && /* @__PURE__ */ o.jsx("span", { children: Al(u.setupSnapshot ?? u.setup, "detectorPreset", "detectorLabel") }),
    u.staleSetup && /* @__PURE__ */ o.jsx("span", { className: "warning", children: "Different setup" }),
    u.sourceRunId && /* @__PURE__ */ o.jsxs("span", { children: [
      "Source ",
      u.sourceRunId
    ] }),
    w && /* @__PURE__ */ o.jsxs("span", { title: w, children: [
      "Checkpoint ",
      w.slice(0, 12),
      "…"
    ] }),
    v.slice(0, 3).map(([E, R]) => {
      const T = x && E === "sourceModel";
      return /* @__PURE__ */ o.jsx("span", { children: T ? /* @__PURE__ */ o.jsxs("b", { children: [
        Rn(E),
        ": ",
        String(R)
      ] }) : `${Rn(E)}: ${String(R)}` }, E);
    })
  ] });
}
function bf({ timings: u }) {
  if (!u) return null;
  const c = [["generation", u.generationSeconds], ["detection", u.detectionSeconds], ["total", u.totalSeconds]].map(([x, w]) => [x, De(w)]).filter(([, x]) => x !== null);
  return c.length ? /* @__PURE__ */ o.jsx("div", { className: "latency-strip", "aria-label": "Run latency", children: c.map(([x, w], v) => /* @__PURE__ */ o.jsxs("span", { children: [
    v > 0 ? "· " : "",
    x,
    " ",
    /* @__PURE__ */ o.jsxs("b", { children: [
      w.toFixed(1),
      "s"
    ] })
  ] }, x)) }) : null;
}
function Zl({ run: u, motion: a, answerAlreadyStreamed: c = !1, onAction: x, onPrepareRerun: w }) {
  var G, Fe, Ve, ze;
  const v = u.analysis ?? u.result ?? {}, E = v.scoreSemantics ?? u.scoreSemantics, R = v.score ?? v.confidence ?? u.score, T = Yo(E, v.scaleLabel ?? u.scaleLabel), k = (v.segments ?? []).some((ne) => De(ne.score) !== null || ne.verdict === !0), U = v.verdict ?? u.verdict, q = v.label ?? (typeof U == "string" ? U : null) ?? (u.status === "failed" ? "Failed" : "Result"), X = u.origin === cc, oe = !X && /replay|recorded/i.test(`${u.origin ?? ""} ${u.mode ?? ""}`), [me] = le.useState(() => {
    const ne = !lc.has(u.id);
    return lc.add(u.id), ne;
  }), K = a !== "static" && !Jl() && me, Z = oe && K && !c, [ee, Ce] = le.useState(!Z), fe = De(v.threshold), ve = (v.segments ?? []).filter((ne) => Bl(De(ne.score), ne.verdict, fe)).length, Re = k && K, Se = dc + ve * fc + Uf, ge = typeof u.error == "string" ? u.error : (G = u.error) == null ? void 0 : G.message, se = u.error && typeof u.error == "object" ? u.error : null;
  return /* @__PURE__ */ o.jsxs("section", { className: `result-card ${Kl(U ?? q)}${Re ? " is-reveal" : ""}`, style: Re ? { "--reveal-total": `${Se}ms` } : void 0, "aria-live": "polite", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "result-heading", children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Outcome" }),
        /* @__PURE__ */ o.jsx("h2", { children: q }),
        /* @__PURE__ */ o.jsx("p", { children: v.summary ?? (u.status === "partial" ? "The answer was preserved, but part of analysis did not complete." : "Evidence is shown in the answer and details below.") })
      ] }),
      !k && De(R) !== null && T && /* @__PURE__ */ o.jsxs("div", { className: "score-orb", children: [
        /* @__PURE__ */ o.jsx("strong", { children: Er(R, E) }),
        /* @__PURE__ */ o.jsx("span", { children: T }),
        ["thresholded_raw_score", "thresholdedRawScore"].includes(E ?? "") && fe !== null && /* @__PURE__ */ o.jsxs("small", { className: "decision-band", children: [
          "vs τ ",
          fe.toFixed(2)
        ] })
      ] })
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "answer-block", children: [
      /* @__PURE__ */ o.jsxs("div", { className: "answer-label", children: [
        /* @__PURE__ */ o.jsx("span", { children: "Answer" }),
        /* @__PURE__ */ o.jsx("small", { children: X ? If.recordedResultVerified : oe ? "Recorded answer · live detection" : u.origin === "importedSnapshot" || u.origin === "imported" ? "Imported snapshot" : /answerability/i.test(u.origin ?? u.mode ?? "") ? "Answerability · live detection" : /supplied/i.test(u.origin ?? u.mode ?? "") ? "Supplied answer · live detection" : "Generated now" })
      ] }),
      !k && (((Fe = v.contextChunkScores) == null ? void 0 : Fe.length) ?? 0) > 1 && /* @__PURE__ */ o.jsx(Kf, { chunks: v.contextChunkScores, semantics: E }),
      Z && !ee ? /* @__PURE__ */ o.jsx(vc, { answer: u.answer ?? "", onComplete: () => Ce(!0) }) : /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
        /* @__PURE__ */ o.jsx(Jf, { answer: u.answer ?? "", result: v }),
        k && /* @__PURE__ */ o.jsx(Qf, { result: v })
      ] })
    ] }),
    v.unavailableReason && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice warning", children: [
      /* @__PURE__ */ o.jsx("b", { children: "Analysis unavailable" }),
      /* @__PURE__ */ o.jsx("span", { children: v.unavailableReason })
    ] }),
    ge && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice error", children: [
      /* @__PURE__ */ o.jsx("b", { children: u.status === "partial" ? "Detection did not finish" : "Run failed" }),
      /* @__PURE__ */ o.jsx("span", { children: ge }),
      (se == null ? void 0 : se.correlationId) && !qf.has(se.code ?? "") && /* @__PURE__ */ o.jsxs("small", { children: [
        "Reference ",
        se.correlationId
      ] })
    ] }),
    (Ve = u.warnings) == null ? void 0 : Ve.map((ne, we) => /* @__PURE__ */ o.jsx("div", { className: "inline-notice warning", children: ne }, we)),
    /* @__PURE__ */ o.jsx(Gf, { result: v }),
    /* @__PURE__ */ o.jsx(Yf, { run: u }),
    /* @__PURE__ */ o.jsx(bf, { timings: u.timings }),
    /* @__PURE__ */ o.jsxs("div", { className: "result-actions", children: [
      X && ((ze = u.inputs) == null ? void 0 : ze.exampleId) && /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", title: "Replays the verified answer and runs the probe live. Loads the model.", onClick: () => {
        var ne, we, Pe;
        return x("submit", { task: "faithfulness", mode: "recordedReplay", context: ((ne = u.inputs) == null ? void 0 : ne.context) ?? "", question: ((we = u.inputs) == null ? void 0 : we.question) ?? "", suppliedAnswer: u.answer ?? "", prompt: "", exampleId: (Pe = u.inputs) == null ? void 0 : Pe.exampleId });
      }, children: [
        /* @__PURE__ */ o.jsx(He, { name: "spark" }),
        "Run it live"
      ] }),
      (u.status === "partial" || u.status === "failed") && u.answer && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", onClick: () => x("retryDetection", { runId: u.id }), children: "Retry detection" }),
      (u.origin === "importedSnapshot" || u.origin === "imported" || u.immutable) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", onClick: () => w(u), children: "Rerun with current setup" }),
      /* @__PURE__ */ o.jsxs("button", { type: "button", className: "quiet", onClick: () => x("exportRun", { runId: u.id }), children: [
        /* @__PURE__ */ o.jsx(He, { name: "download" }),
        "Export run"
      ] })
    ] })
  ] });
}
function _f({ payload: u, draft: a, setDraft: c, busy: x, motion: w, onAction: v, onPrepareRerun: E, onCompare: R }) {
  var Q, _, $;
  const T = u.capabilities ?? {}, k = T, U = String(((Q = u.setup) == null ? void 0 : Q.task) ?? "faithfulness"), q = U === a.task ? !0 : { enabled: !1, reason: `The active detector supports ${Ko(U)}, not ${Ko(a.task)}.` }, X = a.task === "answerability" ? k.canAnswerability ?? q : q, oe = a.task === "faithfulness" && a.mode === "generate" ? T.canGenerate : !0, me = a.prompt.trim().length > 0 || a.context.trim().length > 0 && a.question.trim().length > 0, K = Ae(X) && Ae(oe) && me && (a.task === "answerability" || a.mode === "generate" || a.answer.trim().length > 0), Z = u.availablePresets ?? [], ee = u.replayTarget ?? null, Ce = ((_ = u.viewState) == null ? void 0 : _.showExamples) !== !1, [fe, ve] = le.useState(!1), [Re, Se] = le.useState(""), ge = () => {
    const M = Re || Z[0];
    !M || !K || x || R(M, {
      task: a.task,
      context: a.context,
      question: a.question,
      suppliedAnswer: a.mode === "supplied" ? a.answer : "",
      prompt: a.prompt,
      exampleId: a.exampleId
    });
  }, se = u.examples ?? [], G = se.find((M) => M.id === a.exampleId), Fe = !!(G && (G.recordedAnswer || G.answer)), Ve = !!u.hosted, ze = (G == null ? void 0 : G.recordedAnswer) ?? (G == null ? void 0 : G.answer) ?? "", ne = Ve && !!G && Fe, [we, Pe] = le.useState(null), [Te, ue] = le.useState(null), O = Ve && x && !!we, z = (($ = u.activity) == null ? void 0 : $.runId) ?? null;
  le.useEffect(() => {
    O && z && ue(z);
  }, [O, z]), le.useEffect(() => {
    x || Pe(null);
  }, [x]);
  const P = () => {
    x || !G || (Pe(ze), v("submit", { task: G.task ?? "faithfulness", mode: "recordedReplay", context: a.context, question: a.question, suppliedAnswer: ze, prompt: "", exampleId: G.id }));
  }, h = () => c({ task: a.task, mode: a.mode, exampleId: null, context: "", question: "", answer: "", prompt: "", sourceRunId: null }, !0), S = (M) => c({
    task: M.task ?? a.task,
    mode: a.mode,
    exampleId: M.id,
    context: M.context ?? "",
    question: M.question ?? "",
    answer: M.answer ?? M.recordedAnswer ?? "",
    prompt: M.prompt ?? "",
    sourceRunId: null
  }, !0), J = (M) => {
    if (M.preventDefault(), x) return;
    if (ne) {
      P();
      return;
    }
    if (!K) return;
    const b = a.task === "answerability" ? "answerability" : a.sourceRunId && a.prompt && !a.context && !a.question ? "quickPrompt" : a.mode === "generate" ? "generateAndScore" : "scoreSuppliedAnswer";
    v("submit", {
      task: a.task,
      mode: b,
      context: a.context,
      question: a.question,
      suppliedAnswer: a.mode === "supplied" ? a.answer : "",
      prompt: a.prompt,
      exampleId: a.exampleId,
      ...a.sourceRunId ? { sourceRunId: a.sourceRunId } : {}
    }), a.sourceRunId && c({ ...a, sourceRunId: null });
  };
  if (ee) {
    const M = () => v("submit", { task: "faithfulness", mode: "recordedReplay", context: ee.context, question: ee.question, suppliedAnswer: ee.answer, prompt: "", exampleId: ee.exampleId });
    return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content analyze-workspace", children: [
      /* @__PURE__ */ o.jsxs("form", { className: "analysis-form", onSubmit: (b) => b.preventDefault(), children: [
        /* @__PURE__ */ o.jsxs("div", { className: "inline-notice info", children: [
          /* @__PURE__ */ o.jsx("b", { children: "Recorded result" }),
          /* @__PURE__ */ o.jsx("span", { children: "This detector needs local model weights the hosted demo doesn't ship, so it replays a verified recorded case. For live scoring, pick a Judge — API preset." })
        ] }),
        /* @__PURE__ */ o.jsx(kn, { label: "Context", hint: `${ee.context.length.toLocaleString()} characters`, children: /* @__PURE__ */ o.jsx("textarea", { rows: 7, value: ee.context, readOnly: !0 }) }),
        /* @__PURE__ */ o.jsx(kn, { label: "Question", children: /* @__PURE__ */ o.jsx("textarea", { rows: 2, value: ee.question, readOnly: !0 }) }),
        /* @__PURE__ */ o.jsx(kn, { label: "Recorded answer", children: /* @__PURE__ */ o.jsx("textarea", { rows: 4, value: ee.answer, readOnly: !0 }) }),
        /* @__PURE__ */ o.jsxs("div", { className: "form-actions", children: [
          /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", disabled: !0, title: "Live scoring is unavailable for this preset on the hosted demo — use Replay recorded answer.", children: [
            /* @__PURE__ */ o.jsx(He, { name: "spark" }),
            "Generate & score"
          ] }),
          /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", disabled: x, onClick: M, children: [
            /* @__PURE__ */ o.jsx(He, { name: "spark" }),
            "Replay recorded answer"
          ] })
        ] })
      ] }),
      x ? /* @__PURE__ */ o.jsx(Xl, { activity: u.activity, runs: u.runs ?? [] }) : u.selectedRun ? /* @__PURE__ */ o.jsx(Zl, { run: u.selectedRun, motion: w, onAction: v, onPrepareRerun: E }, u.selectedRun.id) : /* @__PURE__ */ o.jsxs("section", { className: "result-placeholder", children: [
        /* @__PURE__ */ o.jsx("div", { children: /* @__PURE__ */ o.jsx(He, { name: "spark" }) }),
        /* @__PURE__ */ o.jsx("h2", { children: "Your evidence map will appear here." }),
        /* @__PURE__ */ o.jsx("p", { children: "Replay the recorded answer to see this preset's graded result." })
      ] })
    ] });
  }
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content analyze-workspace", children: [
    Ce && /* @__PURE__ */ o.jsx(Bf, { examples: se.filter((M) => !M.task || M.task === a.task), selected: a.exampleId, hosted: Ve, onSelect: S, onCustom: h }),
    /* @__PURE__ */ o.jsxs("form", { className: "analysis-form", onSubmit: J, children: [
      /* @__PURE__ */ o.jsxs("div", { className: "form-row", children: [
        /* @__PURE__ */ o.jsx(kn, { label: "Task", children: /* @__PURE__ */ o.jsxs(Hl, { value: a.task, onChange: (M) => {
          const b = M.target.value;
          c({ ...a, task: b, mode: b === "answerability" ? "generate" : a.mode }, !0);
        }, children: [
          /* @__PURE__ */ o.jsx("option", { value: "faithfulness", disabled: U !== "faithfulness", children: "Hallucination" }),
          /* @__PURE__ */ o.jsx("option", { value: "answerability", disabled: !Ae(k.canAnswerability ?? U === "answerability"), children: "Answerability" })
        ] }) }),
        a.task === "faithfulness" && /* @__PURE__ */ o.jsx(kn, { label: "Answer source", children: /* @__PURE__ */ o.jsxs(Hl, { value: a.mode, onChange: (M) => c({ ...a, mode: M.target.value }, !0), children: [
          /* @__PURE__ */ o.jsx("option", { value: "generate", disabled: !Ae(T.canGenerate), children: "Generate an answer" }),
          /* @__PURE__ */ o.jsx("option", { value: "supplied", children: "Score supplied answer" })
        ] }) })
      ] }),
      a.prompt && /* @__PURE__ */ o.jsxs("details", { className: "prompt-disclosure", children: [
        /* @__PURE__ */ o.jsxs("summary", { children: [
          /* @__PURE__ */ o.jsx("svg", { className: "disclosure-chevron", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: /* @__PURE__ */ o.jsx("path", { d: "m9 18 6-6-6-6" }) }),
          /* @__PURE__ */ o.jsx("span", { children: "Exact model prompt" }),
          /* @__PURE__ */ o.jsxs("span", { className: "disclosure-count", children: [
            a.prompt.length.toLocaleString(),
            " characters"
          ] })
        ] }),
        /* @__PURE__ */ o.jsx(kn, { label: "Prompt", children: /* @__PURE__ */ o.jsx("textarea", { rows: 5, value: a.prompt, placeholder: "Verified example or imported prompt…", onChange: (M) => c({ ...a, prompt: M.target.value, exampleId: null }), onBlur: () => c(a, !0) }) })
      ] }),
      /* @__PURE__ */ o.jsx(kn, { label: "Context", hint: `${a.context.length.toLocaleString()} characters`, children: /* @__PURE__ */ o.jsx("textarea", { rows: 7, value: a.context, placeholder: "Paste the source material the answer must stay grounded in…", onChange: (M) => c({ ...a, context: M.target.value, exampleId: null }), onBlur: () => c(a, !0) }) }),
      /* @__PURE__ */ o.jsx(kn, { label: "Question", children: /* @__PURE__ */ o.jsx("textarea", { rows: 2, value: a.question, placeholder: "What should the model answer from this context?", onChange: (M) => c({ ...a, question: M.target.value, exampleId: null }), onBlur: () => c(a, !0) }) }),
      a.task === "faithfulness" && a.mode === "supplied" && /* @__PURE__ */ o.jsx(kn, { label: "Answer to score", children: /* @__PURE__ */ o.jsx("textarea", { rows: 4, value: a.answer, placeholder: "Paste the answer that should be checked…", onChange: (M) => c({ ...a, answer: M.target.value }), onBlur: () => c(a, !0) }) }),
      !Ae(X) && /* @__PURE__ */ o.jsx("p", { className: "field-error", children: sc(X) ?? "The active detector does not support this task." }),
      !Ae(oe) && /* @__PURE__ */ o.jsx("p", { className: "field-error", children: sc(oe) ?? "Generation is not available with the active setup." }),
      a.sourceRunId && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice info", children: [
        /* @__PURE__ */ o.jsx("b", { children: "Imported run prepared" }),
        /* @__PURE__ */ o.jsx("span", { children: "Review these inputs, then submit explicitly with the current setup." })
      ] }),
      /* @__PURE__ */ o.jsxs("div", { className: "form-actions", children: [
        ne ? /* @__PURE__ */ o.jsxs("button", { className: "primary", type: "button", disabled: x, onClick: P, children: [
          /* @__PURE__ */ o.jsx(He, { name: "spark" }),
          "Replay & score"
        ] }) : /* @__PURE__ */ o.jsxs("button", { className: "primary", type: "submit", disabled: !K || x, children: [
          /* @__PURE__ */ o.jsx(He, { name: "spark" }),
          a.task === "answerability" ? "Check answerability" : a.mode === "supplied" ? "Score answer" : "Generate & score"
        ] }),
        !ne && Fe && /* @__PURE__ */ o.jsxs("button", { type: "button", className: "secondary", disabled: x, onClick: () => v("submit", { task: (G == null ? void 0 : G.task) ?? "faithfulness", mode: "recordedReplay", context: a.context, question: a.question, suppliedAnswer: (G == null ? void 0 : G.recordedAnswer) ?? (G == null ? void 0 : G.answer) ?? "", prompt: "", exampleId: G == null ? void 0 : G.id }), children: [
          /* @__PURE__ */ o.jsx(He, { name: "spark" }),
          "Replay recorded answer"
        ] }),
        Z.length > 0 && /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", disabled: x, "aria-expanded": fe, onClick: () => ve((M) => !M), children: "Compare detectors…" })
      ] }),
      fe && Z.length > 0 && /* @__PURE__ */ o.jsxs("div", { className: "compare-picker", children: [
        /* @__PURE__ */ o.jsx(kn, { label: "Second detector (B)", hint: "scores the same answer", children: /* @__PURE__ */ o.jsx(Hl, { ariaLabel: "Second detector for comparison", value: Re || Z[0], onChange: (M) => Se(M.target.value), children: Z.map((M) => /* @__PURE__ */ o.jsx("option", { value: M, children: M }, M)) }) }),
        /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", disabled: !K || x, onClick: ge, children: [
          /* @__PURE__ */ o.jsx(He, { name: "spark" }),
          "Run comparison"
        ] }),
        !K && /* @__PURE__ */ o.jsx("p", { className: "field-error", children: "Enter a context and question (or an answer to score) first." })
      ] })
    ] }),
    O ? /* @__PURE__ */ o.jsx(Zf, { answer: we ?? "", motion: w }) : x ? /* @__PURE__ */ o.jsx(Xl, { activity: u.activity, runs: u.runs ?? [] }) : u.selectedRun ? /* @__PURE__ */ o.jsx(Zl, { run: u.selectedRun, motion: w, answerAlreadyStreamed: Te === u.selectedRun.id, onAction: v, onPrepareRerun: E }, u.selectedRun.id) : /* @__PURE__ */ o.jsxs("section", { className: "result-placeholder", children: [
      /* @__PURE__ */ o.jsx("div", { children: /* @__PURE__ */ o.jsx(He, { name: "spark" }) }),
      /* @__PURE__ */ o.jsx("h2", { children: "Your evidence map will appear here." }),
      /* @__PURE__ */ o.jsx("p", { children: "Results lead with the outcome, then reveal only the detail each detector can honestly support." })
    ] })
  ] });
}
function $f({ agreement: u }) {
  const a = [
    { key: "both", label: "Both flag", count: u.both, color: "var(--span-line-high)" },
    { key: "aOnly", label: "A only", count: u.aOnly, color: "var(--span-line-low)" },
    { key: "bOnly", label: "B only", count: u.bOnly, color: "var(--brand)" },
    { key: "neither", label: "Neither", count: u.neither, color: "var(--safe)" }
  ], c = a.reduce((v, E) => v + E.count, 0), x = c || 1, w = (v) => Math.round(v / x * 100);
  return /* @__PURE__ */ o.jsxs("div", { className: "agreement", children: [
    /* @__PURE__ */ o.jsxs("p", { className: "eyebrow", children: [
      "Localization agreement · ",
      c,
      " characters"
    ] }),
    /* @__PURE__ */ o.jsx("div", { className: "agreement-bar", role: "img", "aria-label": a.map((v) => `${v.label} ${v.count}`).join(", "), children: a.map((v) => v.count > 0 ? /* @__PURE__ */ o.jsx("span", { style: { width: `${v.count / x * 100}%`, background: v.color }, title: `${v.label}: ${v.count} (${w(v.count)}%)` }, v.key) : null) }),
    /* @__PURE__ */ o.jsx("div", { className: "agreement-legend", children: a.map((v) => /* @__PURE__ */ o.jsxs("span", { children: [
      /* @__PURE__ */ o.jsx("i", { style: { background: v.color }, "aria-hidden": "true" }),
      v.label,
      " ",
      /* @__PURE__ */ o.jsx("b", { children: v.count }),
      " ",
      /* @__PURE__ */ o.jsxs("em", { children: [
        w(v.count),
        "%"
      ] })
    ] }, v.key)) })
  ] });
}
function ep({ compare: u }) {
  const a = De(u.deltaScore);
  return /* @__PURE__ */ o.jsxs("section", { className: "compare-verdict", children: [
    u.agreement ? /* @__PURE__ */ o.jsx($f, { agreement: u.agreement }) : /* @__PURE__ */ o.jsxs("div", { className: "compare-note", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Localization agreement" }),
      /* @__PURE__ */ o.jsx("p", { children: u.agreementNote ?? "No per-character overlap is available for these detectors." })
    ] }),
    /* @__PURE__ */ o.jsx("div", { className: "compare-delta", children: a !== null ? /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsxs("span", { className: "compare-delta-value", children: [
        a > 0 ? "+" : "",
        a.toFixed(2)
      ] }),
      /* @__PURE__ */ o.jsx("span", { children: u.deltaNote })
    ] }) : /* @__PURE__ */ o.jsx("span", { className: "compare-note-line", children: u.deltaNote || "Different score scales — localization overlap only." }) })
  ] });
}
function uc({ label: u, preset: a, run: c, motion: x, onAction: w, onPrepareRerun: v }) {
  var k, U;
  const E = ((k = c == null ? void 0 : c.analysis) == null ? void 0 : k.scoreSemantics) ?? ((U = c == null ? void 0 : c.setupSnapshot) == null ? void 0 : U.scoreSemantics), R = Yo(E), T = c ? ["queued", "running"].includes(c.status) : !1;
  return /* @__PURE__ */ o.jsxs("section", { className: "compare-column", children: [
    /* @__PURE__ */ o.jsxs("header", { className: "compare-col-head", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: u }),
      /* @__PURE__ */ o.jsx("h3", { children: a ?? "Detector" }),
      R && /* @__PURE__ */ o.jsx("small", { children: R })
    ] }),
    c ? T ? /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
      /* @__PURE__ */ o.jsx("h2", { children: "Scoring…" }),
      /* @__PURE__ */ o.jsx("p", { children: "Running this detector over the shared answer." })
    ] }) : /* @__PURE__ */ o.jsx(Zl, { run: c, motion: x, onAction: w, onPrepareRerun: v }, c.id) : /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
      /* @__PURE__ */ o.jsx("h2", { children: "Waiting…" }),
      /* @__PURE__ */ o.jsx("p", { children: "This side scores the same answer once it is available." })
    ] })
  ] });
}
function np({ payload: u, motion: a, onAction: c, onPrepareRerun: x, onBack: w }) {
  const v = u.compare;
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content compare-workspace", children: [
    /* @__PURE__ */ o.jsx("div", { className: "compare-head", children: /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", onClick: w, children: "← Back to Analyze" }) }),
    v ? /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx(ep, { compare: v }),
      /* @__PURE__ */ o.jsxs("div", { className: "compare-grid", children: [
        /* @__PURE__ */ o.jsx(uc, { label: "Detector A", preset: v.presetA, run: v.runA, motion: a, onAction: c, onPrepareRerun: x }),
        /* @__PURE__ */ o.jsx(uc, { label: "Detector B", preset: v.presetB, run: v.runB, motion: a, onAction: c, onPrepareRerun: x })
      ] })
    ] }) : /* @__PURE__ */ o.jsxs("section", { className: "result-placeholder", children: [
      /* @__PURE__ */ o.jsx("div", { children: /* @__PURE__ */ o.jsx(He, { name: "spark" }) }),
      /* @__PURE__ */ o.jsx("h2", { children: "No comparison yet." }),
      /* @__PURE__ */ o.jsx("p", { children: "Open “Compare detectors…” in Analyze to score one answer with two detectors side by side." })
    ] })
  ] });
}
function tp(u) {
  if (!u) return "Time unavailable";
  const a = new Date(u);
  return Number.isNaN(a.valueOf()) ? u : new Intl.DateTimeFormat(void 0, { dateStyle: "medium", timeStyle: "short" }).format(a);
}
function rp({ runs: u, selectedId: a, onSelect: c, onAnalyze: x }) {
  const [w, v] = le.useState(""), [E, R] = le.useState("all"), T = u.filter((k) => (E === "all" || k.status === E) && `${k.title ?? ""} ${k.question ?? ""} ${k.prompt ?? ""} ${k.answer ?? ""}`.toLowerCase().includes(w.toLowerCase()));
  return /* @__PURE__ */ o.jsxs("section", { className: "run-browser", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "section-heading", children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "History" }),
        /* @__PURE__ */ o.jsxs("h2", { children: [
          u.length,
          " ",
          u.length === 1 ? "run" : "runs"
        ] })
      ] }),
      /* @__PURE__ */ o.jsxs("div", { className: "filters", children: [
        /* @__PURE__ */ o.jsx("input", { type: "search", "aria-label": "Search runs", value: w, placeholder: "Search runs", onChange: (k) => v(k.target.value) }),
        /* @__PURE__ */ o.jsxs(Hl, { ariaLabel: "Filter runs by status", value: E, onChange: (k) => R(k.target.value), children: [
          /* @__PURE__ */ o.jsx("option", { value: "all", children: "All outcomes" }),
          /* @__PURE__ */ o.jsx("option", { value: "succeeded", children: "Succeeded" }),
          /* @__PURE__ */ o.jsx("option", { value: "partial", children: "Partial" }),
          /* @__PURE__ */ o.jsx("option", { value: "failed", children: "Failed" }),
          /* @__PURE__ */ o.jsx("option", { value: "interrupted", children: "Interrupted" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ o.jsx("div", { className: "run-list", children: T.length ? T.map((k) => /* @__PURE__ */ o.jsxs("button", { type: "button", className: a === k.id ? "selected" : "", onClick: () => c(k), children: [
      /* @__PURE__ */ o.jsx(mc, { status: k.status }),
      /* @__PURE__ */ o.jsxs("span", { children: [
        /* @__PURE__ */ o.jsx("b", { children: k.title ?? k.question ?? k.prompt ?? `Run ${k.id}` }),
        /* @__PURE__ */ o.jsxs("small", { children: [
          tp(k.completedAt ?? k.createdAt),
          " · ",
          Ko(k.task),
          " · ",
          Rn(k.status)
        ] })
      ] }),
      /* @__PURE__ */ o.jsx("strong", { children: typeof k.verdict == "boolean" ? k.task === "answerability" ? k.verdict ? "Answerable" : "Unanswerable" : k.verdict ? "Unsupported" : "Supported" : k.verdict ?? Er(k.score, k.scoreSemantics) }),
      /* @__PURE__ */ o.jsx(He, { name: "arrow" })
    ] }, k.id)) : u.length === 0 ? /* @__PURE__ */ o.jsxs("div", { className: "empty-list", children: [
      "No runs yet — ",
      /* @__PURE__ */ o.jsx("button", { type: "button", className: "empty-link", onClick: x, children: "analyze a case" }),
      " to get started."
    ] }) : /* @__PURE__ */ o.jsx("div", { className: "empty-list", children: "No runs match these filters." }) })
  ] });
}
function lp({ disabled: u, onImport: a }) {
  const c = le.useRef(null), [x, w] = le.useState(""), v = async (E) => {
    if (E) {
      if (E.size > 10 * 1024 * 1024) {
        w("Portable bundles must be 10 MiB or smaller.");
        return;
      }
      w(""), a(await E.text(), E.name), c.current && (c.current.value = "");
    }
  };
  return /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
    /* @__PURE__ */ o.jsx("input", { ref: c, hidden: !0, type: "file", accept: "application/json,.json", onChange: (E) => {
      var R;
      return void v((R = E.target.files) == null ? void 0 : R[0]);
    } }),
    /* @__PURE__ */ o.jsxs("button", { type: "button", className: "secondary", disabled: u, onClick: () => {
      var E;
      return (E = c.current) == null ? void 0 : E.click();
    }, children: [
      /* @__PURE__ */ o.jsx(He, { name: "upload" }),
      "Import JSON"
    ] }),
    x && /* @__PURE__ */ o.jsx("span", { className: "field-error", role: "alert", children: x })
  ] });
}
function ip({ payload: u, quickPrompt: a, setQuickPrompt: c, selectedId: x, setSelectedId: w, busy: v, motion: E, onAction: R, onPrepareRerun: T, onAnalyze: k }) {
  var oe, me, K, Z;
  const U = u.runs ?? [], q = u.selectedRun ?? U.find((ee) => ee.id === x) ?? null, X = String(((oe = u.setup) == null ? void 0 : oe.task) ?? "faithfulness") === "faithfulness";
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content runs-workspace", children: [
    /* @__PURE__ */ o.jsxs("form", { className: "quick-run", onSubmit: (ee) => {
      ee.preventDefault(), a.trim() && !v && X && R("submit", { task: "faithfulness", mode: "quickPrompt", context: "", question: "", suppliedAnswer: "", prompt: a, exampleId: null });
    }, children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Quick run" }),
        /* @__PURE__ */ o.jsx("h2", { children: "Ask without building a thread." }),
        /* @__PURE__ */ o.jsx("p", { children: "Each prompt becomes an independent, auditable run." })
      ] }),
      /* @__PURE__ */ o.jsx(kn, { label: "Prompt", children: /* @__PURE__ */ o.jsx("textarea", { rows: 3, value: a, placeholder: "Ask the active generator…", onChange: (ee) => c(ee.target.value), onBlur: () => c(a, !0) }) }),
      /* @__PURE__ */ o.jsxs("div", { className: "form-actions", children: [
        /* @__PURE__ */ o.jsxs("button", { type: "submit", className: "primary", title: X ? void 0 : "Quick Run requires a hallucination detector.", disabled: !a.trim() || v || !Ae((me = u.capabilities) == null ? void 0 : me.canGenerate) || !X, children: [
          /* @__PURE__ */ o.jsx(He, { name: "spark" }),
          "Run prompt"
        ] }),
        /* @__PURE__ */ o.jsx(lp, { disabled: !Ae((K = u.capabilities) == null ? void 0 : K.canImport), onImport: (ee) => R("import", { json: ee }) }),
        /* @__PURE__ */ o.jsxs("button", { type: "button", className: "quiet", disabled: !U.length || !Ae((Z = u.capabilities) == null ? void 0 : Z.canExport), onClick: () => R("exportBundle", {}), children: [
          /* @__PURE__ */ o.jsx(He, { name: "download" }),
          "Export session"
        ] })
      ] })
    ] }),
    v && /* @__PURE__ */ o.jsx(Xl, { activity: u.activity, runs: u.runs ?? [] }),
    /* @__PURE__ */ o.jsxs("div", { className: "runs-grid", children: [
      /* @__PURE__ */ o.jsx(rp, { runs: U, selectedId: (q == null ? void 0 : q.id) ?? x, onSelect: (ee) => {
        w(ee.id), R("selectRun", { runId: ee.id });
      }, onAnalyze: k }),
      /* @__PURE__ */ o.jsx("aside", { className: "run-detail", children: q ? /* @__PURE__ */ o.jsx(Zl, { run: q, motion: E, onAction: R, onPrepareRerun: T }, q.id) : /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
        /* @__PURE__ */ o.jsx("h2", { children: "Select a run" }),
        /* @__PURE__ */ o.jsx("p", { children: "Its outcome, evidence, and provenance will appear here." })
      ] }) })
    ] })
  ] });
}
function op(u) {
  return u ? Array.isArray(u) ? u : Object.entries(u).map(([a, c]) => ({ label: Rn(a), value: typeof c == "object" ? JSON.stringify(c) : c })) : [];
}
function sp({ diagnostics: u }) {
  var c;
  const a = u == null ? void 0 : u.attention;
  return (c = a == null ? void 0 : a.values) != null && c.length ? /* @__PURE__ */ o.jsxs("section", { className: "attention-card", children: [
    /* @__PURE__ */ o.jsx("div", { className: "section-heading", children: /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Attention" }),
      /* @__PURE__ */ o.jsx("h2", { children: a.title ?? "Bounded attention summary" })
    ] }) }),
    /* @__PURE__ */ o.jsx("div", { className: "table-scroll", children: /* @__PURE__ */ o.jsxs("table", { children: [
      /* @__PURE__ */ o.jsx("thead", { children: /* @__PURE__ */ o.jsxs("tr", { children: [
        /* @__PURE__ */ o.jsx("th", { children: "Token" }),
        (a.columnLabels ?? []).map((x, w) => /* @__PURE__ */ o.jsx("th", { children: x }, `${x}-${w}`))
      ] }) }),
      /* @__PURE__ */ o.jsx("tbody", { children: a.values.map((x, w) => {
        var v;
        return /* @__PURE__ */ o.jsxs("tr", { children: [
          /* @__PURE__ */ o.jsx("th", { children: ((v = a.rowLabels) == null ? void 0 : v[w]) ?? w + 1 }),
          x.map((E, R) => /* @__PURE__ */ o.jsx("td", { style: E === null ? void 0 : { "--attention": String(Math.max(0, Math.min(1, E))) }, children: /* @__PURE__ */ o.jsx("span", { children: E === null ? "—" : E.toFixed(2) }) }, R))
        ] }, w);
      }) })
    ] }) }),
    a.note && /* @__PURE__ */ o.jsx("p", { className: "caption", children: a.note })
  ] }) : /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
    /* @__PURE__ */ o.jsx("h2", { children: "No attention summary yet" }),
    /* @__PURE__ */ o.jsx("p", { children: "Attention summaries appear here when the active detector captures them." })
  ] });
}
function up({ recipe: u }) {
  const [a, c] = le.useState(!1), x = () => {
    var w, v;
    (v = (w = globalThis.navigator) == null ? void 0 : w.clipboard) == null || v.writeText(u.code).then(
      () => {
        c(!0), globalThis.setTimeout(() => c(!1), 1500);
      },
      () => {
      }
    );
  };
  return /* @__PURE__ */ o.jsxs("article", { className: "recipe-card", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "recipe-head", children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("h3", { children: u.title }),
        /* @__PURE__ */ o.jsx("p", { children: u.description })
      ] }),
      /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", onClick: x, "aria-label": `Copy the ${u.title} snippet`, children: a ? "Copied" : "Copy" })
    ] }),
    u.reference && /* @__PURE__ */ o.jsxs("p", { className: "recipe-reference", children: [
      "Reference: ",
      /* @__PURE__ */ o.jsx("code", { children: u.reference })
    ] }),
    /* @__PURE__ */ o.jsx("pre", { className: "recipe-code", children: /* @__PURE__ */ o.jsx("code", { children: u.code }) })
  ] });
}
function ap({ recipes: u }) {
  return u.length ? /* @__PURE__ */ o.jsxs("section", { className: "recipes-section", children: [
    /* @__PURE__ */ o.jsx("div", { className: "section-heading", children: /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Extend" }),
      /* @__PURE__ */ o.jsx("h2", { children: "Add a detector" }),
      /* @__PURE__ */ o.jsx("p", { children: "Copy-paste starting points — each snippet is real SIRIN API you can adapt." })
    ] }) }),
    /* @__PURE__ */ o.jsx("div", { className: "recipe-list", children: u.map((a) => /* @__PURE__ */ o.jsx(up, { recipe: a }, a.id)) })
  ] }) : null;
}
function cp({ payload: u, busy: a, onAction: c }) {
  var R;
  const x = u.diagnostics, w = u.capabilities ?? {}, v = x != null && x.metrics ? op(x.metrics) : [
    { label: "Runtime", value: (x == null ? void 0 : x.runtime) ?? "Python" },
    { label: "Device", value: (x == null ? void 0 : x.device) ?? "Loads on first run" },
    { label: "Model", value: (x == null ? void 0 : x.activeModel) ?? (x != null && x.modelLoaded ? "Loaded" : "Loads on first run") },
    { label: "Attention", value: x != null && x.attentionAvailable ? "Available" : "Not captured in this mode" }
  ], E = !!((R = u.capabilities) != null && R.trustedLocal);
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content diagnostics-workspace", children: [
    !E && /* @__PURE__ */ o.jsx("div", { className: "privacy-banner", children: /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("b", { children: "Shared-safe diagnostics" }),
      /* @__PURE__ */ o.jsx("span", { children: "Sensitive paths, traces, provider responses, and raw runtime errors remain hidden." })
    ] }) }),
    a && /* @__PURE__ */ o.jsx(Xl, { activity: u.activity, runs: u.runs ?? [] }),
    E && (Ae(w.canRefreshDiagnostics, !1) || Ae(w.canOpenCachedAttention, !1) || Ae(w.canOpenLiveAttention, !1) || Ae(w.canUnloadModels, !1)) && /* @__PURE__ */ o.jsxs("div", { className: "diagnostic-actions", children: [
      Ae(w.canRefreshDiagnostics, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("refreshDiagnostics", {}), children: "Refresh runtime" }),
      Ae(w.canOpenCachedAttention, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("openCachedAttention", {}), children: "Cached attention explorer" }),
      Ae(w.canOpenLiveAttention, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("openLiveAttention", {}), children: "Live attention capture" }),
      Ae(w.canUnloadModels, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", disabled: a, onClick: () => c("unloadModels", {}), children: "Unload models" })
    ] }),
    /* @__PURE__ */ o.jsx("section", { className: "metric-grid", children: v.length ? v.map((T) => /* @__PURE__ */ o.jsxs("article", { className: Kl(T.status), children: [
      /* @__PURE__ */ o.jsx("span", { children: T.label }),
      /* @__PURE__ */ o.jsx("strong", { children: T.value === null ? "Not captured in this mode" : String(T.value) }),
      T.detail && /* @__PURE__ */ o.jsx("small", { children: T.detail })
    ] }, T.label)) : /* @__PURE__ */ o.jsxs("article", { children: [
      /* @__PURE__ */ o.jsx("span", { children: "Runtime status" }),
      /* @__PURE__ */ o.jsx("strong", { children: (x == null ? void 0 : x.status) ?? "Ready" }),
      /* @__PURE__ */ o.jsx("small", { children: "Refresh to request a safe server summary." })
    ] }) }),
    (x == null ? void 0 : x.message) && /* @__PURE__ */ o.jsx("div", { className: "inline-notice info", children: x.message }),
    /* @__PURE__ */ o.jsx(sp, { diagnostics: x }),
    E && (x == null ? void 0 : x.details) && /* @__PURE__ */ o.jsxs("details", { className: "diagnostic-details", children: [
      /* @__PURE__ */ o.jsx("summary", { children: "Trusted-local details" }),
      /* @__PURE__ */ o.jsx("dl", { children: Object.entries(x.details).map(([T, k]) => /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("dt", { children: Rn(T) }),
        /* @__PURE__ */ o.jsx("dd", { children: typeof k == "object" ? JSON.stringify(k) : String(k) })
      ] }, T)) })
    ] }),
    /* @__PURE__ */ o.jsx(ap, { recipes: u.recipes ?? [] })
  ] });
}
function dp(u) {
  try {
    const a = URL.createObjectURL(new Blob([u.content], { type: u.mimeType ?? "application/json" })), c = document.createElement("a");
    return c.href = a, c.download = u.fileName, c.click(), setTimeout(() => URL.revokeObjectURL(a), 0), !0;
  } catch {
    return !1;
  }
}
function fp({ componentKey: u, payload: a, setStateValue: c, setTriggerValue: x }) {
  var Ve, ze, ne, we, Pe, Te, ue, O;
  const w = a.viewState, v = ql.get(u) ?? { sequence: 0, draft: Af(a.draft), workspace: (w == null ? void 0 : w.workspace) ?? "analyze", appearance: (w == null ? void 0 : w.appearance) ?? Vf, selectedRunId: null, seenDownload: null, focusWorkspace: null };
  ql.has(u) || ql.set(u, v);
  const [E, R] = le.useState(v.workspace), [T, k] = le.useState(v.appearance), [U, q] = le.useState(v.draft), [X, oe] = le.useState(v.selectedRunId), [me, K] = le.useState(!1), Z = le.useRef(null), ee = (Ve = a.actionReceipt) == null ? void 0 : Ve.sequence;
  le.useEffect(() => K(!1), [ee, (ze = a.activity) == null ? void 0 : ze.status, a.runsRevision]), le.useEffect(() => {
    w != null && w.workspace && w.workspace !== v.workspace && (v.workspace = w.workspace, R(w.workspace)), w != null && w.appearance && (w.appearance.theme !== v.appearance.theme || w.appearance.motion !== v.appearance.motion) && (v.appearance = w.appearance, k(w.appearance));
  }, [w == null ? void 0 : w.workspace, (ne = w == null ? void 0 : w.appearance) == null ? void 0 : ne.theme, (we = w == null ? void 0 : w.appearance) == null ? void 0 : we.motion, v]), le.useEffect(() => {
    if (T.motion !== "lively" || Jl()) return;
    const z = () => {
      new Image().src = ac;
    };
    if (globalThis.requestIdleCallback) {
      const h = globalThis.requestIdleCallback(z);
      return () => globalThis.cancelIdleCallback(h);
    }
    const P = globalThis.setTimeout(z, 2e3);
    return () => globalThis.clearTimeout(P);
  }, [T.motion]), le.useEffect(() => {
    document.documentElement.dataset.sirinMotion = T.motion;
  }, [T.motion]), le.useEffect(() => {
    var h;
    const z = v.focusWorkspace;
    if (!z || (w == null ? void 0 : w.workspace) !== z) return;
    const P = (h = Z.current) == null ? void 0 : h.querySelector(`[data-workspace-tab="${z}"]`);
    P && (P.focus(), v.focusWorkspace = null);
  }, [w == null ? void 0 : w.workspace, v]), le.useEffect(() => {
    if (!a.download) {
      v.seenDownload = null;
      return;
    }
    const z = a.download ? `${a.download.fileName}:${a.download.content.length}` : null;
    if (a.download && z !== v.seenDownload && (v.seenDownload = z, dp(a.download))) {
      v.sequence += 1;
      const P = { protocolVersion: a.protocolVersion, clientInstanceId: ic(), sequence: v.sequence, actionId: oc(), type: "clearDownload", expectedSetupRevision: a.setupRevision, expectedRunsRevision: a.runsRevision, payload: {} };
      x("action", P);
    }
  }, [a.download, a.protocolVersion, a.setupRevision, a.runsRevision, v, x]);
  const Ce = me || ["queued", "running"].includes(((Pe = a.activity) == null ? void 0 : Pe.status) ?? ""), fe = (z) => {
    v.workspace = z, v.focusWorkspace = z, R(z), x("viewState", { workspace: z, appearance: v.appearance });
  }, ve = (z, P = !1) => {
    const h = { ...U, analyze: z };
    v.draft = h, q(h), P && c("draft", h);
  }, Re = (z, P = !1) => {
    const h = { ...U, quickPrompt: z };
    v.draft = h, q(h), P && c("draft", h);
  }, Se = (z) => {
    v.selectedRunId = z, oe(z), c("selectedRunId", z);
  }, ge = (z) => {
    var J;
    const P = z.inputs ?? {}, S = { task: ((J = z.setupSnapshot) == null ? void 0 : J.task) ?? z.task ?? "faithfulness", mode: P.suppliedAnswer ? "supplied" : "generate", exampleId: null, context: P.context ?? "", question: P.question ?? "", answer: P.suppliedAnswer ?? "", prompt: P.prompt ?? "", sourceRunId: z.id };
    ve(S, !0), fe("analyze");
  }, se = (z, P) => {
    if (Ce && z !== "selectRun") return;
    v.sequence += 1;
    const h = { protocolVersion: a.protocolVersion, clientInstanceId: ic(), sequence: v.sequence, actionId: oc(), type: z, expectedSetupRevision: a.setupRevision, expectedRunsRevision: a.runsRevision, payload: P };
    K(!["selectRun"].includes(z)), x("action", h);
  }, G = (z, P) => {
    fe("compare"), se("runCompare", { inputs: P, presetB: z });
  }, Fe = a.notices ?? [];
  return /* @__PURE__ */ o.jsx("div", { ref: Z, className: "sirin-workspace", "data-theme": T.theme, "data-motion": T.motion, children: /* @__PURE__ */ o.jsxs("div", { className: "shell", children: [
    /* @__PURE__ */ o.jsx(Hf, { workspace: E, onWorkspace: fe, setup: a.setup, title: (Te = a.ui) == null ? void 0 : Te.title, subtitle: (ue = a.ui) == null ? void 0 : ue.subtitle, busy: Ce, motion: T.motion }),
    Fe.length > 0 && /* @__PURE__ */ o.jsx("div", { className: "notice-stack", "aria-live": "polite", children: Fe.map((z, P) => /* @__PURE__ */ o.jsxs("div", { className: `inline-notice ${z.level ?? z.kind ?? "info"}`, children: [
      z.title && /* @__PURE__ */ o.jsx("b", { children: z.title }),
      /* @__PURE__ */ o.jsx("span", { children: z.message })
    ] }, P)) }),
    ((O = a.actionReceipt) == null ? void 0 : O.status) === "rejected" && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice error receipt", role: "alert", children: [
      /* @__PURE__ */ o.jsx("b", { children: "Action rejected" }),
      /* @__PURE__ */ o.jsx("span", { children: a.actionReceipt.message ?? "The request could not be accepted." })
    ] }),
    E === "analyze" && /* @__PURE__ */ o.jsx(_f, { payload: a, draft: U.analyze, setDraft: ve, busy: Ce, motion: T.motion, onAction: se, onPrepareRerun: ge, onCompare: G }),
    E === "runs" && /* @__PURE__ */ o.jsx(ip, { payload: a, quickPrompt: U.quickPrompt, setQuickPrompt: Re, selectedId: X, setSelectedId: Se, busy: Ce, motion: T.motion, onAction: se, onPrepareRerun: ge, onAnalyze: () => fe("analyze") }),
    E === "compare" && /* @__PURE__ */ o.jsx(np, { payload: a, motion: T.motion, onAction: se, onPrepareRerun: ge, onBack: () => fe("analyze") }),
    E === "diagnostics" && /* @__PURE__ */ o.jsx(cp, { payload: a, busy: Ce, onAction: se }),
    /* @__PURE__ */ o.jsxs("footer", { children: [
      /* @__PURE__ */ o.jsxs("span", { children: [
        "SIRIN — ",
        /* @__PURE__ */ o.jsx("a", { href: "https://github.com/sb-ai-lab/SIRIN", target: "_blank", rel: "noreferrer", children: "github.com/sb-ai-lab/SIRIN" })
      ] }),
      /* @__PURE__ */ o.jsx("span", { children: "Detector confidence is not automatically a calibrated probability." })
    ] })
  ] }) });
}
const Cr = /* @__PURE__ */ new WeakMap(), Rr = /* @__PURE__ */ new Map();
function pp(u) {
  for (const [a, c] of Rr)
    a !== u && !c.isConnected && (ql.delete(a), Rr.delete(a));
}
const hp = ({ data: u, key: a, parentElement: c, setStateValue: x, setTriggerValue: w }) => {
  Df(), Wf(c);
  let v = Cr.get(c);
  if (v && (!v.container.isConnected || v.container.parentNode !== c)) {
    try {
      v.root.unmount();
    } catch {
    }
    v.container.remove(), Cr.delete(c), v = void 0;
  }
  if (!v) {
    c.querySelectorAll(".sirin-component-root").forEach((T) => T.remove());
    const R = document.createElement("div");
    R.className = "sirin-component-root", c.append(R), v = { container: R, root: Sf.createRoot(R) }, Cr.set(c, v);
  }
  Rr.set(a, v.container), pp(a);
  const E = v;
  return E.root.render(/* @__PURE__ */ o.jsx(fp, { componentKey: a, payload: u, setStateValue: x, setTriggerValue: w })), () => {
    Cr.get(c) === E && (Cr.delete(c), Rr.get(a) === E.container && Rr.delete(a), E.root.unmount(), E.container.remove());
  };
};
export {
  hp as default
};
